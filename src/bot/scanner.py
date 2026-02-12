"""
🔍 Market Tarayıcı
Top 100 coin'i sürekli tarar, strateji sinyallerini üretir
"""
import pandas as pd
import logging
import time
from .exchange import ExchangeClient
from .strategy import generate_signal, calculate_indicators
from .config import TIMEFRAME, OHLCV_LIMIT, TOP_COINS_COUNT

logger = logging.getLogger("scanner")


class MarketScanner:
    """Sürekli çalışan piyasa tarayıcı"""

    def __init__(self, exchange: ExchangeClient):
        self.exchange = exchange
        self.symbols: list[str] = []
        self.last_refresh = 0
        self.refresh_interval = 3600  # Her saat coin listesini yenile

    def refresh_symbols(self):
        """Top coin listesini güncelle"""
        now = time.time()
        if now - self.last_refresh < self.refresh_interval and self.symbols:
            return

        logger.info(f"🔄 Top {TOP_COINS_COUNT} coin listesi yenileniyor...")
        self.symbols = self.exchange.fetch_top_futures_symbols(TOP_COINS_COUNT)
        self.last_refresh = now
        logger.info(f"✅ {len(self.symbols)} coin yüklendi")

    def scan_symbol(self, symbol: str) -> dict | None:
        """Tek bir coin'i tara ve sinyal üret"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, TIMEFRAME, OHLCV_LIMIT)
            if not ohlcv or len(ohlcv) < 50:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            signal = generate_signal(df, symbol)
            return signal

        except Exception as e:
            logger.debug(f"⚠️ {symbol} tarama hatası: {e}")
            return None

    def scan_all(self) -> list[dict]:
        """Tüm coinleri tara, sinyalleri topla"""
        self.refresh_symbols()
        signals = []

        for i, symbol in enumerate(self.symbols):
            signal = self.scan_symbol(symbol)
            if signal:
                signals.append(signal)

            # Rate limit koruması
            if (i + 1) % 10 == 0:
                time.sleep(0.5)

        # Skora göre sırala (en yüksek önce)
        signals.sort(key=lambda s: s['score'], reverse=True)

        if signals:
            logger.info(f"🎯 {len(signals)} sinyal bulundu (top: {signals[0]['symbol']} skor:{signals[0]['score']})")
        else:
            logger.info("🔍 Sinyal bulunamadı")

        return signals
