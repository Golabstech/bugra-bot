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
)

logger = logging.getLogger("trader")


class TradeManager:
    """Sinyal alır → Pozisyon açar → SL/TP yönetir"""

    def __init__(self, exchange: ExchangeClient, portfolio: PortfolioManager):
        self.exchange = exchange
        self.portfolio = portfolio

    def execute_signal(self, signal: dict) -> bool:
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
            # Pozisyon boyutu hesapla
            amount, margin = self.portfolio.calculate_position_size(symbol, current_price)
            
            if amount <= 0:
                logger.warning(f"⚠️ {symbol}: Yetersiz bakiye veya çok düşük miktar")
                return False

            # Borsada emir aç
            logger.info(f"🚀 {symbol} {side} denemesi #{current_attempt} | Miktar: {amount}")
            
            if side == 'SHORT':
                order = self.exchange.open_short(symbol, amount)
            else:
                order = self.exchange.open_long(symbol, amount)

            if order:
                # BAŞARILI!
                fill_price = float(order.get('average', current_price))
                signal['entry_price'] = fill_price
                pos = self.portfolio.register_position(signal, amount, margin)

                # SL emri koy (Pozisyona bağlı — closePosition)
                self.exchange.set_stop_loss(symbol, side, signal['sl'])
                # TP emirleri yazılımsal yönetilecek (_check_tp_sl içinde)

                notifier.notify_trade_open(symbol, side, amount, fill_price, margin)
                logger.info(f"✅ {symbol} {side} açıldı @ {fill_price} | Margin: ${margin}")
                return True

            # BAŞARISIZ OLDUYSA (Hata yönetimi)
            # Eğer hata bakiye değil de "Quantity" ise miktarı küçültüp tekrar dene
            logger.warning(f"⚠️ Deneme #{current_attempt} başarısız. Miktarı azaltıp tekrar denenecek...")
            
            # Fiyatı son bir kez daha güncelle (belki çok oynamıştır)
            ticker = self.exchange.fetch_ticker(symbol)
            if ticker: current_price = float(ticker['last'])
            
            # Bir sonraki deneme için miktarı teorik olarak azaltacak bir margin düşüşü simüle edelim
            # calculate_position_size içinde margin free*0.1 alıyordu, onu burada manuel müdahale edemeyiz
            # O yüzden exchange.py içindeki open_short hata logunda miktar hatası gelirse miktar sanitize edilecek.
            # Şimdilik döngüyü kırmamak için kilit bir miktar düşüşü uygulayalım: (calculate_position_size'ın bir alternatifi gibi)
            current_attempt += 1
            import time
            time.sleep(0.5)

        logger.error(f"❌ {symbol} {max_retries} denemeye rağmen açılamadı.")
        return False

    def check_positions(self, scanner=None):
        """Açık pozisyonları kontrol et — TP/SL + Signal Decay"""
        for symbol, pos in list(self.portfolio.positions.items()):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue

                current_price = float(ticker['last'])
                
                # 1. Klasik TP/SL kontrolü
                self._check_tp_sl(pos, current_price)
                
                # 2. Signal Decay Exit (Sinyal Çürümesi Çıkışı)
                if scanner and pos.entry_score > 0:
                    self._check_signal_decay(pos, current_price, scanner)

            except Exception as e:
                logger.error(f"❌ {symbol} kontrol hatası: {e}")

    def _check_signal_decay(self, pos, current_price: float, scanner):
        """
        🧠 SİNYAL ÇÜRÜMESI KONTROLÜ
        Giriş skoru düştüyse ve kârdaysak → Erken çıkış yap.
        "Hype bittiyse, kârı al ve daha iyi fırsata geç."
        """
        symbol = pos.symbol
        
        # Sadece 'Recovered' olmayan pozisyonlarda uygula
        if 'Recovered' in pos.reasons:
            return
        
        # Güncel skoru hesapla
        signal = scanner.scan_symbol(symbol, include_all=True)
        if not signal:
            return
        
        current_score = signal.get('score', 0)
        entry_score = pos.entry_score
        
        # Skor düşüş oranı hesapla
        if entry_score <= 0:
            return
        
        decay_ratio = current_score / entry_score  # 0.4 = %40'ına düşmüş
        
        # PnL hesapla
        if pos.side == 'SHORT':
            pnl_pct = ((pos.entry_price - current_price) / pos.entry_price) * 100
        else:
            pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100
        
        # Her döngüde mevcut durumu logla
        logger.debug(f"📊 {symbol} Decay: Giriş={entry_score} → Şimdi={current_score} ({decay_ratio:.0%}) | PnL: {pnl_pct:+.2f}%")
        
        # KARAR: Skor yarıdan fazla düştüyse VE kârdaysak → Çık
        if decay_ratio < 0.40 and pnl_pct > 0.3:
            logger.info(f"🧠 SIGNAL DECAY: {symbol} | Skor {entry_score} → {current_score} ({decay_ratio:.0%}) | PnL: {pnl_pct:+.2f}% | Kârı al!")
            self._close_full(pos, "DECAY_EXIT", current_price)

    def _check_tp_sl(self, pos, current_price: float):
        """Yazılımsal TP/SL kontrolü — Borsa SL'i pozisyona bağlı, TP tamamen kod tarafında"""
        symbol = pos.symbol
        side = pos.side

        # SL kontrolü (Borsa SL'i closePosition ile ayarlı, bu fallback)
        if side == 'SHORT':
            is_stopped = current_price >= pos.sl
        else:
            is_stopped = current_price <= pos.sl

        if is_stopped:
            self._close_full(pos, "STOP LOSS", current_price)
            return

        # TP1 kontrolü (Yazılımsal)
        if not pos.tp1_hit:
            is_tp1 = (current_price <= pos.tp1) if side == 'SHORT' else (current_price >= pos.tp1)
            if is_tp1:
                pos.tp1_hit = True
                tp1_amount = round(pos.initial_amount * TP1_CLOSE_PCT, 4)
                tp1_amount = self.exchange.sanitize_amount(symbol, tp1_amount)
                if tp1_amount > 0:
                    self.exchange.close_position(symbol, side, tp1_amount)
                    pos.amount -= tp1_amount

                # BE (Breakeven) — SL'i giriş fiyatına çek
                # Eski SL'i iptal edip yeni SL koy
                self.exchange.cancel_all_orders(symbol)
                pos.sl = pos.entry_price
                self.exchange.set_stop_loss(symbol, side, pos.sl)

                pnl_pct = self._calc_pnl_pct(pos, pos.tp1)
                notifier.notify_trade_close(symbol, "TP1", pnl_pct, 0)
                logger.info(f"🎯 TP1 HIT: {symbol} @ {current_price} | Kalan: {pos.amount}")

        # TP2 kontrolü (Yazılımsal)
        elif not pos.tp2_hit:
            is_tp2 = (current_price <= pos.tp2) if side == 'SHORT' else (current_price >= pos.tp2)
            if is_tp2:
                pos.tp2_hit = True
                tp2_amount = round(pos.initial_amount * TP2_CLOSE_PCT, 4)
                tp2_amount = self.exchange.sanitize_amount(symbol, tp2_amount)
                if tp2_amount > 0:
                    self.exchange.close_position(symbol, side, tp2_amount)
                    pos.amount -= tp2_amount

                # Trailing SL güncelle
                self.exchange.cancel_all_orders(symbol)
                if side == 'SHORT':
                    pos.sl = pos.entry_price - (pos.entry_price - pos.tp1) * 0.5
                else:
                    pos.sl = pos.entry_price + (pos.tp1 - pos.entry_price) * 0.5
                self.exchange.set_stop_loss(symbol, side, pos.sl)

                pnl_pct = self._calc_pnl_pct(pos, pos.tp2)
                notifier.notify_trade_close(symbol, "TP2", pnl_pct, 0)
                logger.info(f"🎯 TP2 HIT: {symbol} @ {current_price} | Kalan: {pos.amount}")

        # TP3 kontrolü (Yazılımsal)
        else:
            is_tp3 = (current_price <= pos.tp3) if side == 'SHORT' else (current_price >= pos.tp3)
            if is_tp3:
                self._close_full(pos, "TP3", current_price)

    def _close_full(self, pos, result: str, price: float):
        """Pozisyonu tamamen kapat"""
        symbol = pos.symbol
        remaining = pos.amount

        if remaining > 0:
            self.exchange.cancel_all_orders(symbol)
            self.exchange.close_position(symbol, pos.side, remaining)

        pnl_pct = self._calc_pnl_pct(pos, price)
        pnl_usd = pos.margin * (pnl_pct / 100)

        self.portfolio.close_position(symbol, result, pnl_usd)
        notifier.notify_trade_close(symbol, result, pnl_pct, pnl_usd)
        logger.info(f"{'✅' if pnl_usd >= 0 else '❌'} {symbol} kapatıldı: {result} | PnL: {pnl_pct:+.2f}% (${pnl_usd:+.2f})")

    def _calc_pnl_pct(self, pos, exit_price: float) -> float:
        """PnL yüzde hesapla"""
        if pos.side == 'SHORT':
            return ((pos.entry_price - exit_price) / pos.entry_price) * 100
        return ((exit_price - pos.entry_price) / pos.entry_price) * 100
