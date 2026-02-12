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
        
        # 🛡️ FİLTRE LİSTESİ (Stabil ve Pegged Coinler)
        self.IGNORED_COINS = {
            'USDC', 'FDUSD', 'TUSD', 'USDP', 'DAI', 'EUR', 'BUSD', 'USDD', 'PYUSD',
            'WBTC', 'BTCST', 'BETH' # Pegged varlıklar (Hareketi ana coine bağlı)
        }
        self.IGNORED_KEYWORDS = ['DOWN', 'UP', 'BEAR', 'BULL'] # Kaldıraçlı token isimleri
        self.last_refresh = 0
        self.refresh_interval = 3600  # Her saat coin listesini yenile

    def refresh_symbols(self):
        """Top coin listesini güncelle"""
        now = time.time()
        if now - self.last_refresh < self.refresh_interval and self.symbols:
            return

        logger.info(f"🔄 Top {TOP_COINS_COUNT} coin listesi yenileniyor...")
        
        try:
            # Tüm futures sembollerini ve hacimlerini çek
            tickers_list = self.exchange.client.fapiPublicGetTicker24hr()
        except Exception as e:
            logger.error(f"⚠️ Futures ticker bilgileri çekilirken hata oluştu: {e}")
            return

        # Hacme göre sırala
        tickers_list.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        
        top_coins = []
        limit = TOP_COINS_COUNT
        for t in tickers_list:
            symbol = t['symbol']
            
            # 🛡️ FİLTRELEME MANTIĞI
            # USDT paritelerini hedefliyoruz ve base asset'i çıkarıyoruz
            if not symbol.endswith('USDT'):
                continue

            base_asset = symbol.replace('USDT', '')
            
            # 1. Stabil Coin Kontrolü
            if base_asset in self.IGNORED_COINS:
                continue
                
            # 2. İsim Kontrolü (DOWN/UP vb.)
            if any(k in base_asset for k in self.IGNORED_KEYWORDS):
                continue
            
            # 3. Hacim Kontrolü (Çok düşük hacimli = Delist riski / Manipülasyon)
            quote_vol = float(t.get('quoteVolume', 0))
            if quote_vol < 5_000_000: # 5 Milyon dolar altı hacim riskli
                continue
            
            top_coins.append(symbol)
            if len(top_coins) >= limit:
                break
        
        self.symbols = top_coins
        self.last_refresh = now
        logger.info(f"✅ {len(self.symbols)} coin yüklendi (Filtrelendi)")

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
```
