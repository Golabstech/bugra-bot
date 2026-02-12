"""
💼 Portföy & Risk Yönetimi
Dinamik marjin, pozisyon takibi, günlük kayıp limiti
"""
import logging
from datetime import datetime, timezone
from .config import (
    POSITION_SIZE_PCT, LEVERAGE, MAX_RISK_PCT,
    MAX_CONCURRENT_POSITIONS, DAILY_LOSS_LIMIT_PCT,
    COIN_BLACKLIST_AFTER, COIN_BLACKLIST_CANDLES,
    COOLDOWN_CANDLES, HARD_STOP_LOSS_PCT,
    TP1_CLOSE_PCT, TP2_CLOSE_PCT, TP3_CLOSE_PCT,
)

logger = logging.getLogger("portfolio")


class Position:
    """Tek bir açık pozisyon"""
    def __init__(self, symbol: str, side: str, entry_price: float,
                 amount: float, margin: float, sl: float,
                 tp1: float, tp2: float, tp3: float, reasons: list):
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.amount = amount
        self.initial_amount = amount
        self.margin = margin
        self.sl = sl
        self.tp1 = tp1
        self.tp2 = tp2
        self.tp3 = tp3
        self.reasons = reasons
        self.tp1_hit = False
        self.tp2_hit = False
        self.opened_at = datetime.now(timezone.utc)
        self.sl_order_id = None
        self.tp_order_ids = []

    @property
    def remaining_pct(self) -> float:
        if self.tp2_hit:
            return TP3_CLOSE_PCT
        if self.tp1_hit:
            return 1.0 - TP1_CLOSE_PCT
        return 1.0

    def __repr__(self):
        return f"<Position {self.symbol} {self.side} @ {self.entry_price} | Remaining: {self.remaining_pct:.0%}>"


class PortfolioManager:
    """Portföy ve risk yönetim motoru"""

    def __init__(self, exchange_client):
        self.exchange = exchange_client
        self.positions: dict[str, Position] = {}
        self.daily_pnl = 0.0
        self.daily_trades = {'wins': 0, 'losses': 0}
        self.daily_reset_date = datetime.now(timezone.utc).date()
        self.coin_cooldowns: dict[str, datetime] = {}
        self.coin_consecutive_losses: dict[str, int] = {}

    def _reset_daily_if_needed(self):
        """Gün değiştiyse günlük sayaçları sıfırla"""
        today = datetime.now(timezone.utc).date()
        if today != self.daily_reset_date:
            logger.info(f"📅 Yeni gün: {today} — Günlük sayaçlar sıfırlandı")
            self.daily_pnl = 0.0
            self.daily_trades = {'wins': 0, 'losses': 0}
            self.daily_reset_date = today

    def get_balance(self) -> dict:
        """Canlı bakiye bilgisi"""
        return self.exchange.get_balance()

    def can_open_position(self, symbol: str) -> tuple[bool, str]:
        """Yeni pozisyon açılabilir mi? → (ok, reason)"""
        self._reset_daily_if_needed()

        # Zaten hafızada açık mı?
        if symbol in self.positions:
            return False, f"{symbol} zaten açık (hafızada)"

        # Restart durumu: Borsada zaten açık mı?
        exchange_positions = self.exchange.get_positions()
        active_symbols = [p['symbol'] for p in exchange_positions]
        if symbol in active_symbols:
            return False, f"{symbol} zaten açık (borsada)"

        # Max eş zamanlı pozisyon
        if len(self.positions) >= MAX_CONCURRENT_POSITIONS:
            return False, f"Max pozisyon limiti: {MAX_CONCURRENT_POSITIONS}"

        # Günlük kayıp limiti
        balance = self.get_balance()
        total = balance['total']
        if total > 0 and abs(self.daily_pnl) / total * 100 >= DAILY_LOSS_LIMIT_PCT:
            return False, f"Günlük kayıp limiti aşıldı: ${self.daily_pnl:.2f}"

        # Max risk kontrolü
        used_margin = sum(p.margin for p in self.positions.values())
        if total > 0 and used_margin / total * 100 >= MAX_RISK_PCT:
            return False, f"Max risk limiti: kasanın %{MAX_RISK_PCT}'i kullanımda"

        # Coin cooldown
        if symbol in self.coin_cooldowns:
            if datetime.now(timezone.utc) < self.coin_cooldowns[symbol]:
                return False, f"{symbol} blacklist'te (cooldown)"

        return True, "OK"

    def calculate_position_size(self, symbol: str, price: float) -> tuple[float, float]:
        """Pozisyon büyüklüğü hesapla → (amount, margin)"""
        balance = self.get_balance()
        free = balance['free']
        margin = free * (POSITION_SIZE_PCT / 100)

        if margin < 5:
            return 0, 0

        notional = margin * LEVERAGE
        amount = notional / price

        # Binance minimum miktar kontrolü (exchange tarafından da kontrol edilir)
        return round(amount, 4), round(margin, 2)

    def register_position(self, signal: dict, amount: float, margin: float) -> Position:
        """Yeni pozisyonu kaydet"""
        pos = Position(
            symbol=signal['symbol'],
            side=signal['side'],
            entry_price=signal['entry_price'],
            amount=amount,
            margin=margin,
            sl=signal['sl'],
            tp1=signal['tp1'],
            tp2=signal['tp2'],
            tp3=signal['tp3'],
            reasons=signal['reasons'],
        )
        self.positions[signal['symbol']] = pos
        logger.info(f"📋 Pozisyon kayıtlı: {pos}")
        return pos

    def close_position(self, symbol: str, result: str, pnl_usd: float):
        """Pozisyonu kapat ve istatistik güncelle"""
        if symbol not in self.positions:
            return

        self._reset_daily_if_needed()
        self.daily_pnl += pnl_usd

        if pnl_usd >= 0:
            self.daily_trades['wins'] += 1
            self.coin_consecutive_losses[symbol] = 0
        else:
            self.daily_trades['losses'] += 1
            losses = self.coin_consecutive_losses.get(symbol, 0) + 1
            self.coin_consecutive_losses[symbol] = losses

            if losses >= COIN_BLACKLIST_AFTER:
                from datetime import timedelta
                cooldown_minutes = COIN_BLACKLIST_CANDLES * 15  # 15m timeframe
                self.coin_cooldowns[symbol] = datetime.now(timezone.utc) + timedelta(minutes=cooldown_minutes)
                self.coin_consecutive_losses[symbol] = 0
                logger.warning(f"🚫 {symbol} blacklist'e alındı ({cooldown_minutes} dk)")

        del self.positions[symbol]
        logger.info(f"🗑️ Pozisyon silindi: {symbol} | {result} | PnL: ${pnl_usd:+.2f}")

    def get_stats(self) -> dict:
        """Günlük istatistikler"""
        self._reset_daily_if_needed()
        balance = self.get_balance()
        return {
            'balance': balance['total'],
            'free': balance['free'],
            'daily_pnl': self.daily_pnl,
            'open_positions': len(self.positions),
            'wins': self.daily_trades['wins'],
            'losses': self.daily_trades['losses'],
        }
