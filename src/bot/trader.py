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

        # Risk kontrolü
        can_open, reason = self.portfolio.can_open_position(symbol)
        if not can_open:
            logger.info(f"⏭️ {symbol} atlandı: {reason}")
            notifier.notify_risk_limit(f"{symbol}: {reason}")
            return False

        # Pozisyon boyutu hesapla
        amount, margin = self.portfolio.calculate_position_size(
            symbol, signal['entry_price']
        )
        if amount <= 0:
            logger.warning(f"⚠️ {symbol}: Yetersiz bakiye")
            return False

        # Borsada emir aç
        side = signal['side']
        if side == 'SHORT':
            order = self.exchange.open_short(symbol, amount)
        else:
            order = self.exchange.open_long(symbol, amount)

        if not order:
            return False

        # Gerçek dolma fiyatını al
        fill_price = float(order.get('average', signal['entry_price']))

        # Pozisyonu kaydet
        signal['entry_price'] = fill_price
        pos = self.portfolio.register_position(signal, amount, margin)

        # SL emri koy (tüm pozisyon için)
        sl_order = self.exchange.set_stop_loss(symbol, side, signal['sl'], amount)
        if sl_order:
            pos.sl_order_id = sl_order.get('id')

        # TP1 emri koy (kısmi kapatma)
        tp1_amount = round(amount * TP1_CLOSE_PCT, 4)
        tp1_order = self.exchange.set_take_profit(symbol, side, signal['tp1'], tp1_amount)
        if tp1_order:
            pos.tp_order_ids.append(tp1_order.get('id'))

        # Bildirim gönder
        notifier.notify_trade_open(symbol, side, amount, fill_price, margin)
        logger.info(f"✅ {symbol} {side} açıldı @ {fill_price} | Margin: ${margin}")

        return True

    def check_positions(self):
        """Açık pozisyonları kontrol et — TP/SL durumlarını güncelle"""
        for symbol, pos in list(self.portfolio.positions.items()):
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue

                current_price = float(ticker['last'])
                self._check_tp_sl(pos, current_price)

            except Exception as e:
                logger.error(f"❌ {symbol} kontrol hatası: {e}")

    def _check_tp_sl(self, pos, current_price: float):
        """Manuel TP/SL kontrolü (exchange emirleri başarısız olursa fallback)"""
        symbol = pos.symbol
        side = pos.side

        # SL kontrolü
        if side == 'SHORT':
            is_stopped = current_price >= pos.sl
        else:
            is_stopped = current_price <= pos.sl

        if is_stopped:
            self._close_full(pos, "STOP LOSS", current_price)
            return

        # TP1 kontrolü
        if not pos.tp1_hit:
            is_tp1 = (current_price <= pos.tp1) if side == 'SHORT' else (current_price >= pos.tp1)
            if is_tp1:
                pos.tp1_hit = True
                tp1_amount = round(pos.initial_amount * TP1_CLOSE_PCT, 4)
                self.exchange.close_position(symbol, side, tp1_amount)
                pos.amount -= tp1_amount

                # BE (Breakeven) — SL'i giriş fiyatına çek
                self.exchange.cancel_all_orders(symbol)
                pos.sl = pos.entry_price
                self.exchange.set_stop_loss(symbol, side, pos.sl, pos.amount)

                # TP2 emri koy
                tp2_amount = round(pos.initial_amount * TP2_CLOSE_PCT, 4)
                self.exchange.set_take_profit(symbol, side, pos.tp2, tp2_amount)

                pnl_pct = self._calc_pnl_pct(pos, pos.tp1)
                notifier.notify_trade_close(symbol, "TP1", pnl_pct, 0)
                logger.info(f"🎯 TP1 HIT: {symbol} @ {current_price}")

        # TP2 kontrolü
        elif not pos.tp2_hit:
            is_tp2 = (current_price <= pos.tp2) if side == 'SHORT' else (current_price >= pos.tp2)
            if is_tp2:
                pos.tp2_hit = True
                tp2_amount = round(pos.initial_amount * TP2_CLOSE_PCT, 4)
                self.exchange.close_position(symbol, side, tp2_amount)
                pos.amount -= tp2_amount

                # Trailing SL güncelle
                self.exchange.cancel_all_orders(symbol)
                if side == 'SHORT':
                    pos.sl = pos.entry_price - (pos.entry_price - pos.tp1) * 0.5
                else:
                    pos.sl = pos.entry_price + (pos.tp1 - pos.entry_price) * 0.5
                self.exchange.set_stop_loss(symbol, side, pos.sl, pos.amount)

                # TP3 emri koy
                tp3_amount = pos.amount
                self.exchange.set_take_profit(symbol, side, pos.tp3, tp3_amount)

                pnl_pct = self._calc_pnl_pct(pos, pos.tp2)
                notifier.notify_trade_close(symbol, "TP2", pnl_pct, 0)
                logger.info(f"🎯 TP2 HIT: {symbol} @ {current_price}")

        # TP3 kontrolü
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
