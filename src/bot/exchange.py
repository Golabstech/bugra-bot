"""
🔌 Binance Futures Exchange Connector (CCXT)
Paper trading + canlı trading desteği
"""
import ccxt
import logging
from .config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, EXCHANGE_SANDBOX, LEVERAGE
)

logger = logging.getLogger("exchange")


class ExchangeClient:
    """Binance Futures bağlantı katmanı"""

    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_API_SECRET,
            'options': {'defaultType': 'future'},
            'enableRateLimit': True,
        })

        if EXCHANGE_SANDBOX:
            self.exchange.set_sandbox_mode(True)
            logger.info("🧪 PAPER TRADING modu aktif (Binance Testnet)")
        else:
            logger.warning("⚠️ CANLI TRADING modu aktif!")

    def get_balance(self) -> dict:
        """Futures cüzdan bakiyesini döndür"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            return {
                'total': float(usdt.get('total', 0)),
                'free': float(usdt.get('free', 0)),
                'used': float(usdt.get('used', 0)),
            }
        except Exception as e:
            logger.error(f"❌ Bakiye alınamadı: {e}")
            return {'total': 0, 'free': 0, 'used': 0}

    def get_positions(self) -> list:
        """Açık pozisyonları listele"""
        try:
            positions = self.exchange.fetch_positions()
            return [p for p in positions if float(p.get('contracts', 0)) > 0]
        except Exception as e:
            logger.error(f"❌ Pozisyonlar alınamadı: {e}")
            return []

    def set_leverage(self, symbol: str, leverage: int = LEVERAGE):
        """Kaldıracı ayarla"""
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.info(f"⚙️ {symbol} kaldıraç: {leverage}x")
        except Exception as e:
            logger.warning(f"⚠️ {symbol} kaldıraç ayarlanamadı: {e}")

    def set_margin_mode(self, symbol: str, mode: str = "isolated"):
        """Marjin modunu ayarla (isolated/cross)"""
        try:
            self.exchange.set_margin_mode(mode, symbol)
        except Exception as e:
            # Zaten ayarlıysa hata verir, sorun değil
            pass

    def open_short(self, symbol: str, amount: float) -> dict | None:
        """Short pozisyon aç"""
        try:
            self.set_leverage(symbol)
            self.set_margin_mode(symbol)
            order = self.exchange.create_market_sell_order(
                symbol, amount, params={'reduceOnly': False}
            )
            logger.info(f"📉 SHORT açıldı: {symbol} | Miktar: {amount}")
            return order
        except Exception as e:
            logger.error(f"❌ SHORT açılamadı {symbol}: {e}")
            return None

    def open_long(self, symbol: str, amount: float) -> dict | None:
        """Long pozisyon aç"""
        try:
            self.set_leverage(symbol)
            self.set_margin_mode(symbol)
            order = self.exchange.create_market_buy_order(
                symbol, amount, params={'reduceOnly': False}
            )
            logger.info(f"📈 LONG açıldı: {symbol} | Miktar: {amount}")
            return order
        except Exception as e:
            logger.error(f"❌ LONG açılamadı {symbol}: {e}")
            return None

    def close_position(self, symbol: str, side: str, amount: float) -> dict | None:
        """Pozisyonu kapat (kısmi veya tam)"""
        try:
            if side == 'SHORT':
                order = self.exchange.create_market_buy_order(
                    symbol, amount, params={'reduceOnly': True}
                )
            else:
                order = self.exchange.create_market_sell_order(
                    symbol, amount, params={'reduceOnly': True}
                )
            logger.info(f"✅ Pozisyon kapatıldı: {symbol} | {amount}")
            return order
        except Exception as e:
            logger.error(f"❌ Pozisyon kapatılamadı {symbol}: {e}")
            return None

    def set_stop_loss(self, symbol: str, side: str, stop_price: float, amount: float) -> dict | None:
        """Stop loss emri koy"""
        try:
            sl_side = 'buy' if side == 'SHORT' else 'sell'
            order = self.exchange.create_order(
                symbol, 'stop_market', sl_side, amount,
                params={
                    'stopPrice': stop_price,
                    'reduceOnly': True,
                    'closePosition': False,
                }
            )
            logger.info(f"🛑 SL ayarlandı: {symbol} @ {stop_price}")
            return order
        except Exception as e:
            logger.error(f"❌ SL ayarlanamadı {symbol}: {e}")
            return None

    def set_take_profit(self, symbol: str, side: str, tp_price: float, amount: float) -> dict | None:
        """Take profit emri koy"""
        try:
            tp_side = 'buy' if side == 'SHORT' else 'sell'
            order = self.exchange.create_order(
                symbol, 'take_profit_market', tp_side, amount,
                params={
                    'stopPrice': tp_price,
                    'reduceOnly': True,
                    'closePosition': False,
                }
            )
            logger.info(f"🎯 TP ayarlandı: {symbol} @ {tp_price}")
            return order
        except Exception as e:
            logger.error(f"❌ TP ayarlanamadı {symbol}: {e}")
            return None

    def cancel_all_orders(self, symbol: str):
        """Bir sembol için tüm açık emirleri iptal et"""
        try:
            self.exchange.cancel_all_orders(symbol)
            logger.info(f"🗑️ Tüm emirler iptal edildi: {symbol}")
        except Exception as e:
            logger.warning(f"⚠️ Emir iptali başarısız {symbol}: {e}")

    def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> list:
        """OHLCV verisi çek"""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            logger.error(f"❌ OHLCV alınamadı {symbol}: {e}")
            return []

    def fetch_ticker(self, symbol: str) -> dict | None:
        """Anlık fiyat bilgisi"""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"❌ Ticker alınamadı {symbol}: {e}")
            return None

    def fetch_top_futures_symbols(self, count: int = 100) -> list[str]:
        """Hacme göre ilk N futures sembolünü getir"""
        try:
            markets = self.exchange.load_markets()
            futures = {
                s: m for s, m in markets.items()
                if m.get('swap') and m.get('quote') == 'USDT' and m.get('active')
            }

            tickers = self.exchange.fetch_tickers(list(futures.keys()))
            sorted_by_volume = sorted(
                tickers.values(),
                key=lambda t: float(t.get('quoteVolume', 0) or 0),
                reverse=True,
            )
            return [t['symbol'] for t in sorted_by_volume[:count]]
        except Exception as e:
            logger.error(f"❌ Top coinler alınamadı: {e}")
            return []
