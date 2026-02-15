"""
🤖 İşlem Yöneticisi
Sinyal → Emir akışını yönetir, SL/TP emirlerini borsaya iletir
"""
import logging
from .exchange import ExchangeClient
from .portfolio import PortfolioManager
from . import notifier
from .config import (
    STRATEGY_SIDE, TP1_CLOSE_PCT, TP2_CLOSE_PCT, TP3_CLOSE_PCT,
    ENABLE_FLIP_STRATEGY, FLIP_TP1_PCT, FLIP_TP2_PCT, FLIP_SL_PCT,
    TAKER_FEE, TP1_SL_RETRACE, LEVERAGE,
)

logger = logging.getLogger("trader")


class TradeManager:
    """Sinyal alır → Pozisyon açar → SL/TP yönetir"""

    def __init__(self, exchange: ExchangeClient, portfolio: PortfolioManager):
        self.exchange = exchange
        self.portfolio = portfolio

    async def execute_signal(self, signal: dict) -> bool:
        """
        Sinyali işleme al → pozisyon aç, SL/TP emirlerini koy
        Kademeli sinyaller için allocation yüzdesi dikkate alınır
        """
        symbol = signal['symbol']
        side = signal['side']
        
        # Kademeli giriş mi?
        allocation = signal.get('allocation', 1.0)  # Varsayılan %100
        if allocation < 1.0:
            logger.info(f"🎯 {symbol} KADEMELİ GİRİŞ: {allocation:.0%} pozisyon açılacak")

        # 1. Risk kontrolü
        can_open, reason = self.portfolio.can_open_position(symbol)
        if not can_open:
            logger.info(f"⏭️ {symbol} atlandı: {reason}")
            notifier.notify_risk_limit(f"{symbol}: {reason}")
            return False

        # 2. İinatçı Emir Mekanizması (Retry Loop)
        max_retries = 3
        current_attempt = 1
        
        # Sinyaldeki fiyattan başla ama borsa fiyatını çekerek güncelle
        ticker = self.exchange.fetch_ticker(symbol)
        current_price = float(ticker['last']) if ticker else signal['entry_price']

        while current_attempt <= max_retries:
            # Her denemede miktarı biraz daha azalt (%0, %10, %20 düşüş gibi)
            reduction = 1.0 - ((current_attempt - 1) * 0.1)
            
            # Kademeli giriş için allocation faktörünü uygula
            final_allocation = allocation * reduction
            
            # Pozisyon boyutu hesapla (kademeli allocation dahil)
            amount, margin = self.portfolio.calculate_position_size(symbol, current_price, reduction_factor=final_allocation)
            
            if amount <= 0:
                logger.warning(f"⚠️ {symbol}: Miktar çok düşük (Deneme #{current_attempt})")
                return False

            # Borsada emir aç
            logger.info(f"🚀 {symbol} {side} #{current_attempt} | Miktar: {amount} (Alloc: {allocation:.0%}, Red: {reduction:.0%})")
            
            if side == 'SHORT':
                order = self.exchange.open_short(symbol, amount)
            else:
                order = self.exchange.open_long(symbol, amount)

            if order:
                # BAŞARILI!
                fill_price = float(order.get('average', current_price))
                signal['entry_price'] = fill_price
                pos = await self.portfolio.register_position(signal, amount, margin)

                # SL emri koy (Pozisyona bağlı — closePosition)
                self.exchange.set_stop_loss(symbol, side, signal['sl'])
                # TP emirleri yazılımsal yönetilecek (_check_tp_sl içinde)

                notifier.notify_trade_open(symbol, side, amount, fill_price, margin)
                logger.info(f"✅ {symbol} {side} açıldı @ {fill_price} | Margin: ${margin} | {allocation:.0%}")
                return True

            # BAŞARISIZ OLDUYSA (Hata yönetimi)
            logger.warning(f"⚠️ Deneme #{current_attempt} başarısız. Miktar azaltılıp tekrar denenecek...")
            
            # Fiyatı son bir kez daha güncelle
            ticker = self.exchange.fetch_ticker(symbol)
            if ticker: current_price = float(ticker['last'])
            
            current_attempt += 1
            import asyncio
            await asyncio.sleep(1) # Biraz bekle ki borsa kendine gelsin

        logger.error(f"❌ {symbol} {max_retries} denemeye rağmen açılamadı.")
        return False

    async def check_positions(self, scanner=None):
        """Açık pozisyonları kontrol et — TP/SL + Signal Decay + Zaman Limiti"""
        from datetime import datetime, timezone

        for symbol, pos in list(self.portfolio.positions.items()):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue

                current_price = float(ticker['last'])

                # 0. Zaman Bazlı Çıkış (48 saat limiti)
                if pos.opened_at:
                    opened = datetime.fromisoformat(pos.opened_at)
                    age_hours = (datetime.now(timezone.utc) - opened).total_seconds() / 3600
                    if age_hours > 48:
                        pnl_pct = self._calc_pnl_pct(pos, current_price)
                        logger.warning(f"⏰ ZAMAN AŞIMI: {symbol} | {age_hours:.0f}h açık | PnL: {pnl_pct:+.2f}% | Kapatılıyor.")
                        await self._close_full(pos, "TIME_EXIT", current_price)
                        continue
                
                # 1. TP/SL kontrolü
                await self._check_tp_sl(pos, current_price)

            except Exception as e:
                logger.error(f"❌ {symbol} kontrol hatası: {e}")


    async def _check_signal_decay(self, pos, current_price: float, signal: dict):
        """v4.0 optimize: Signal Decay devre dışı bırakıldı"""
        return
        symbol = pos.symbol
        
        # 'Recovered' durumundaki manuel işlemler veya özel durumlar için atla
        if 'Recovered' in pos.reasons:
            return
        
        current_score = signal.get('score', 0)
        entry_score = pos.entry_score
        
        if entry_score <= 0:
            return
        
        # Skor değişim oranı
        ratio = current_score / entry_score
        
        # Mevcut PnL durumu
        if pos.side == 'SHORT':
            pnl_pct = ((pos.entry_price - current_price) / pos.entry_price) * 100
        else:
            pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100
        
        logger.debug(f"📊 {symbol} Mantık Kontrol: Giriş={entry_score} → Şimdi={current_score} ({ratio:.0%}) | PnL: {pnl_pct:+.2f}%")

        # ---------------------------------------------------------------------
        # DURUM 1: SKOR ARTIYOR (SHORT SQUEEZE RİSKİ)
        # ---------------------------------------------------------------------
        # Girdikten sonra skor %20'den fazla arttıysa, bu coin hype kazanmaya devam ediyor demektir.
        # Short işlemde bu tehlikelidir. Stop-loss patlamadan güvenli tahliye.
        if ratio > 1.25 and pnl_pct < -0.5:
             logger.warning(f"🚨 SQUEEZE ALERT: {symbol} | Skor yükseliyor {entry_score} -> {current_score} ({ratio:.0%}) | Trend karşıya dönmüş olabilir, kaç!")
             await self._close_full(pos, "SQUEEZE_EXIT", current_price)
             
             # 🔄 FLIP: Hemen ters yönde Long açmayı dene
             if ENABLE_FLIP_STRATEGY:
                 await self._execute_flip_trade(symbol, "LONG", current_price, current_score)
             return

        # ---------------------------------------------------------------------
        # DURUM 2: SKOR DÜŞÜYOR (HYPE BİTİYOR)
        # ---------------------------------------------------------------------
        if ratio < 0.40:
            # A) POZİSYON KÂRDA (%0.5+) -> Kârı erkenden ALMA, Stop-Loss'u GİRİŞE çek.
            if pnl_pct > 0.5:
                # Sadece eğer stop henüz girişe çekilmediyse
                if (pos.side == 'SHORT' and pos.sl > pos.entry_price) or \
                   (pos.side == 'LONG' and pos.sl < pos.entry_price):
                    
                    logger.info(f"🛡️ TRAILING STOP: {symbol} | Skor düştü {current_score:.0f}, kâr korumaya alınıyor (BE).")
                    pos.sl = pos.entry_price # Stopu girişe çek
                    self.exchange.cancel_all_orders(symbol)
                    self.exchange.set_stop_loss(symbol, pos.side, pos.sl)
                    # Güncellenen SL'i Redis'e yaz
                    from .redis_client import redis_client
                    await redis_client.hset("bot:positions", symbol, pos.to_dict())
            
            # B) POZİSYON ZARARDA VEYA YATAY -> Zaman kaybı yapma, çık.
            elif pnl_pct < 0.2:
                logger.info(f"⏳ VAKİT KAYBI: {symbol} | Skor sönümlendi {current_score:.0f} ve gelişme yok. Çıkılıyor.")
                await self._close_full(pos, "DECAY_EXIT", current_price)


    async def _check_tp_sl(self, pos, current_price: float):
        """Yazılımsal TP/SL kontrolü"""
        symbol = pos.symbol
        side = pos.side
        
        # CRITICAL FIX: Check if position still exists on exchange
        # Exchange SL might have triggered without bot knowing
        exchange_positions = self.exchange.get_positions()
        exchange_symbols = set()
        for p in exchange_positions:
            if float(p.get('contracts', 0)) == 0:
                continue
            sym = p['info'].get('symbol') or p['symbol'].replace('/', '').split(':')[0]
            exchange_symbols.add(sym)
        
        if symbol not in exchange_symbols:
            logger.warning(f"🔔 {symbol} borsada kapanmış (SL/Likidason), senkronize ediliyor")
            # Calculate approximate PnL from last known price
            pnl_pct = self._calc_pnl_pct(pos, current_price)
            pnl_usd = pos.margin * (pnl_pct / 100)
            await self.portfolio.close_position(symbol, "EXCHANGE_CLOSED", pnl_usd)
            return
        
        if side == 'SHORT':
            is_stopped = current_price >= pos.sl
        else:
            is_stopped = current_price <= pos.sl

        if is_stopped:
            await self._close_full(pos, "STOP LOSS", current_price)
            return

        # TP1 kontrolü (Hedef: ATR TP1)
        if not pos.tp1_hit:
            is_tp1 = (current_price <= pos.tp1) if side == 'SHORT' else (current_price >= pos.tp1)
            if is_tp1:
                pos.tp1_hit = True
                tp1_amount = self.exchange.sanitize_amount(symbol, pos.initial_amount * TP1_CLOSE_PCT)
                if tp1_amount > 0:
                    self.exchange.close_position(symbol, side, tp1_amount)
                    # CRITICAL FIX: Prevent negative amount
                    pos.amount = max(0, pos.amount - tp1_amount)

                # CRITICAL FIX: Correct SL trailing for both LONG and SHORT
                # Move SL to entry + (risk * retrace_factor) toward breakeven
                if side == 'LONG':
                    # LONG: SL is below entry, risk = entry - sl (positive)
                    risk = pos.entry_price - pos.sl
                    pos.sl = pos.entry_price - (risk * TP1_SL_RETRACE)
                else:
                    # SHORT: SL is above entry, risk = sl - entry (positive)
                    risk = pos.sl - pos.entry_price
                    pos.sl = pos.entry_price + (risk * TP1_SL_RETRACE)
                
                logger.info(f"🎯 TP1 HIT: {symbol} @ {current_price} | Yeni SL: {pos.sl:.2f}")
                
                # Pozisyon hâlâ açık mı kontrol et
                exchange_positions = self.exchange.get_positions()
                position_exists = any(
                    (p['info'].get('symbol') or p['symbol'].replace('/', '').split(':')[0]) == symbol
                    and float(p.get('contracts', 0)) > 0
                    for p in exchange_positions
                )
                
                if position_exists:
                    self.exchange.cancel_all_orders(symbol)
                    self.exchange.set_stop_loss(symbol, side, pos.sl)
                    
                    from .redis_client import redis_client
                    await redis_client.hset("bot:positions", symbol, pos.to_dict())
                else:
                    logger.info(f"ℹ️ {symbol} pozisyonu zaten kapalı, SL ayarlanmadı")
                
                pnl_pct = self._calc_pnl_pct(pos, current_price)
                realized_pnl_usd = (pos.initial_amount * TP1_CLOSE_PCT) * pos.entry_price * (pnl_pct/100)
                notifier.notify_trade_close(symbol, "TP1", pnl_pct, realized_pnl_usd)

        # TP2 kontrolü (Hedef: ATR TP2)
        elif not pos.tp2_hit:
            is_tp2 = (current_price <= pos.tp2) if side == 'SHORT' else (current_price >= pos.tp2)
            if is_tp2:
                pos.tp2_hit = True
                tp2_amount = self.exchange.sanitize_amount(symbol, pos.initial_amount * TP2_CLOSE_PCT)
                if tp2_amount > 0:
                    self.exchange.close_position(symbol, side, tp2_amount)
                    # CRITICAL FIX: Prevent negative amount
                    pos.amount = max(0, pos.amount - tp2_amount)
                
                logger.info(f"🎯 TP2 HIT: {symbol} @ {current_price} | SL Girişe (BE) çekildi.")
                
                # SL'i GİRİŞE çek (TP2'den sonra artık risk yok)
                pos.sl = pos.entry_price
                
                # Pozisyon hâlâ açık mı kontrol et
                exchange_positions = self.exchange.get_positions()
                position_exists = any(
                    (p['info'].get('symbol') or p['symbol'].replace('/', '').split(':')[0]) == symbol
                    and float(p.get('contracts', 0)) > 0
                    for p in exchange_positions
                )
                
                if position_exists:
                    self.exchange.cancel_all_orders(symbol)
                    self.exchange.set_stop_loss(symbol, side, pos.sl)
                    
                    from .redis_client import redis_client
                    await redis_client.hset("bot:positions", symbol, pos.to_dict())
                else:
                    logger.info(f"ℹ️ {symbol} pozisyonu zaten kapalı, SL ayarlanmadı")
                
                pnl_pct = self._calc_pnl_pct(pos, current_price)
                realized_pnl_usd = (pos.initial_amount * TP2_CLOSE_PCT) * pos.entry_price * (pnl_pct/100)
                notifier.notify_trade_close(symbol, "TP2", pnl_pct, realized_pnl_usd)

        # TP3 kontrolü (Hedef: ATR TP3)
        else:
            is_tp3 = (current_price <= pos.tp3) if side == 'SHORT' else (current_price >= pos.tp3)
            if is_tp3:
                logger.info(f"💰 TP3 HIT: {symbol} @ {current_price} | Pozisyon Kapatılıyor.")
                await self._close_full(pos, "TP3", current_price)

    async def _close_full(self, pos, result: str, price: float):
        """Pozisyonu tamamen kapat"""
        symbol = pos.symbol
        remaining = pos.amount

        if remaining > 0:
            self.exchange.cancel_all_orders(symbol)
            self.exchange.close_position(symbol, pos.side, remaining)

        pnl_pct = self._calc_pnl_pct(pos, price)
        pnl_usd = pos.margin * (pnl_pct / 100)

        await self.portfolio.close_position(symbol, result, pnl_usd)
        notifier.notify_trade_close(symbol, result, pnl_pct, pnl_usd)
        logger.info(f"{'✅' if pnl_usd >= 0 else '❌'} {symbol} kapatıldı: {result} | PnL: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")

    def _calc_pnl_pct(self, pos, exit_price: float) -> float:
        """PnL yüzde hesapla (Fee dahil)"""
        # CRITICAL FIX: Fee is calculated on notional value, not margin
        # With leverage, fee impact is multiplied
        fee_pct = TAKER_FEE * 100 * 2  # Giriş + Çıkış fee (on notional)
        if pos.side == 'SHORT':
            raw = ((pos.entry_price - exit_price) / pos.entry_price) * 100
        else:
            raw = ((exit_price - pos.entry_price) / pos.entry_price) * 100
        # Apply fee on leveraged position (fee eats into margin)
        leveraged_fee_pct = fee_pct * LEVERAGE / 100 * 100  # Convert back to percentage of margin
        return raw - fee_pct  # Fee is already on notional, leverage accounted in raw PnL

    async def _execute_flip_trade(self, symbol: str, side: str, price: float, score: int):
        """
        🚀 FLIP TRADE (Ters Yüz İşlemi)
        Hızlı bir sinyal oluşturup execute_signal'e paslar.
        """
        logger.info(f"🔄 FLIP STRATEGY TETİKLENDİ: {symbol} yön {side} olarak değişiyor!")
        
        # Vur-Kaç SL/TP ayarları
        risk_pct = FLIP_SL_PCT / 100
        tp1_pct = FLIP_TP1_PCT / 100
        tp2_pct = FLIP_TP2_PCT / 100
        
        if side == 'LONG':
            sl = price * (1 - risk_pct)
            tp1 = price * (1 + tp1_pct)
            tp2 = price * (1 + tp2_pct)
            tp3 = price * (1 + (tp2_pct * 1.5)) # TP3 biraz daha uzak
        else: # Genelde short'tan long'a flip olacağı için burası yedek
            sl = price * (1 + risk_pct)
            tp1 = price * (1 - tp1_pct)
            tp2 = price * (1 - tp2_pct)
            tp3 = price * (1 - (tp2_pct * 1.5))

        flip_signal = {
            'symbol': symbol,
            'side': side,
            'score': score,
            'reasons': ['FLIP_SQUEEZE'],
            'entry_price': price,
            'sl': round(sl, 6),
            'tp1': round(tp1, 6),
            'tp2': round(tp2, 6),
            'tp3': round(tp3, 6),
            'atr': 0, # Flip'te ATR yerine yüzde bazlı gidiyoruz
            'is_valid': True
        }
        
        # 1 saniye bekle (Borsanın önceki emri tamamen temizlemesine izin ver)
        import asyncio
        await asyncio.sleep(1)
        
        # Yeni pozisyonu aç
        await self.execute_signal(flip_signal)
