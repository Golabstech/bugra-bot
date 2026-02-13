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
)

logger = logging.getLogger("trader")


class TradeManager:
    """Sinyal alır → Pozisyon açar → SL/TP yönetir"""

    def __init__(self, exchange: ExchangeClient, portfolio: PortfolioManager):
        self.exchange = exchange
        self.portfolio = portfolio

    async def execute_signal(self, signal: dict) -> bool:
        """Sinyali işleme al → pozisyon aç, SL/TP emirlerini koy"""
        symbol = signal['symbol']
        side = signal['side']

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
            
            # Pozisyon boyutu hesapla
            amount, margin = self.portfolio.calculate_position_size(symbol, current_price, reduction_factor=reduction)
            
            if amount <= 0:
                logger.warning(f"⚠️ {symbol}: Miktar çok düşük (Deneme #{current_attempt})")
                return False

            # Borsada emir aç
            logger.info(f"🚀 {symbol} {side} denemesi #{current_attempt} | Miktar: {amount} (Redüksiyon: {reduction:.0%})")
            
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
                logger.info(f"✅ {symbol} {side} açıldı @ {fill_price} | Margin: ${margin}")
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
        """Açık pozisyonları kontrol et — TP/SL + Signal Decay"""
        for symbol, pos in list(self.portfolio.positions.items()):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue

                current_price = float(ticker['last'])
                
                # 1. Klasik TP/SL kontrolü
                await self._check_tp_sl(pos, current_price)
                
                # 2. Signal Decay Exit (Sinyal Çürümesi Çıkışı)
                if scanner and pos.entry_score > 0:
                    await self._check_signal_decay(pos, current_price, scanner)

            except Exception as e:
                logger.error(f"❌ {symbol} kontrol hatası: {e}")

    async def _check_signal_decay(self, pos, current_price: float, scanner):
        """
        🧠 UYARLANABİLİR POZİSYON YÖNETİMİ (Artık sadece decay değil, risk yönetimi)
        1. Skor Artarsa (ratio > 1.2): Short Squeeze riski -> Erken kaç!
        2. Skor Düşerse (ratio < 0.4) + Karşılık: Stopu girişe çek (Trailing Stop active).
        3. Skor Düşerse (ratio < 0.4) + Zarar: Enerjisi bitti -> Vakit kaybı çıkışı.
        """
        symbol = pos.symbol
        
        # 'Recovered' durumundaki manuel işlemler veya özel durumlar için atla
        if 'Recovered' in pos.reasons:
            return
        
        # Güncel skoru hesapla
        signal = scanner.scan_symbol(symbol, include_all=True)
        if not signal:
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
                    # Portfolio objesini güncelle
                    await self.portfolio.register_position(pos.to_dict(), pos.amount, pos.margin)
            
            # B) POZİSYON ZARARDA VEYA YATAY -> Zaman kaybı yapma, çık.
            elif pnl_pct < 0.2:
                logger.info(f"⏳ VAKİT KAYBI: {symbol} | Skor sönümlendi {current_score:.0f} ve gelişme yok. Çıkılıyor.")
                await self._close_full(pos, "DECAY_EXIT", current_price)


    async def _check_tp_sl(self, pos, current_price: float):
        """Yazılımsal TP/SL kontrolü"""
        symbol = pos.symbol
        side = pos.side

        if side == 'SHORT':
            is_stopped = current_price >= pos.sl
        else:
            is_stopped = current_price <= pos.sl

        if is_stopped:
            await self._close_full(pos, "STOP LOSS", current_price)
            return

        # TP1 kontrolü
        if not pos.tp1_hit:
            is_tp1 = (current_price <= pos.tp1) if side == 'SHORT' else (current_price >= pos.tp1)
            if is_tp1:
                pos.tp1_hit = True
                tp1_amount = self.exchange.sanitize_amount(symbol, pos.initial_amount * TP1_CLOSE_PCT)
                if tp1_amount > 0:
                    self.exchange.close_position(symbol, side, tp1_amount)
                    pos.amount -= tp1_amount

                self.exchange.cancel_all_orders(symbol)
                pos.sl = pos.entry_price
                self.exchange.set_stop_loss(symbol, side, pos.sl)
                
                await redis_client.hset("bot:positions", symbol, pos.to_dict())
                pnl_pct = self._calc_pnl_pct(pos, pos.tp1)
                notifier.notify_trade_close(symbol, "TP1", pnl_pct, 0)
                logger.info(f"🎯 TP1 HIT: {symbol} @ {current_price} | Kalan: {pos.amount}")

        # TP2 kontrolü
        elif not pos.tp2_hit:
            is_tp2 = (current_price <= pos.tp2) if side == 'SHORT' else (current_price >= pos.tp2)
            if is_tp2:
                pos.tp2_hit = True
                tp2_amount = self.exchange.sanitize_amount(symbol, pos.initial_amount * TP2_CLOSE_PCT)
                if tp2_amount > 0:
                    self.exchange.close_position(symbol, side, tp2_amount)
                    pos.amount -= tp2_amount

                self.exchange.cancel_all_orders(symbol)
                if side == 'SHORT':
                    pos.sl = pos.entry_price - (pos.entry_price - pos.tp1) * 0.5
                else:
                    pos.sl = pos.entry_price + (pos.tp1 - pos.entry_price) * 0.5
                self.exchange.set_stop_loss(symbol, side, pos.sl)

                await redis_client.hset("bot:positions", symbol, pos.to_dict())
                pnl_pct = self._calc_pnl_pct(pos, pos.tp2)
                notifier.notify_trade_close(symbol, "TP2", pnl_pct, 0)
                logger.info(f"🎯 TP2 HIT: {symbol} @ {current_price} | Kalan: {pos.amount}")

        else:
            is_tp3 = (current_price <= pos.tp3) if side == 'SHORT' else (current_price >= pos.tp3)
            if is_tp3:
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
        """PnL yüzde hesapla"""
        if pos.side == 'SHORT':
            return ((pos.entry_price - exit_price) / pos.entry_price) * 100
        return ((exit_price - pos.entry_price) / pos.entry_price) * 100

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
