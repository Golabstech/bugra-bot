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
            tickers_list = self.exchange.exchange.fapiPublicGetTicker24hr()
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

    def scan_symbol(self, symbol: str, include_all: bool = False) -> dict | None:
        """Tek bir coin'i tara ve sinyal üret"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, TIMEFRAME, OHLCV_LIMIT)
            if not ohlcv or len(ohlcv) < 50:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # Funding Rate çek (Piyasa kalabalık göstergesi)
            funding_rate = self.exchange.fetch_funding_rate(symbol)

            signal = generate_signal(df, symbol, include_all=include_all, funding_rate=funding_rate)
            return signal

        except Exception as e:
            logger.debug(f"⚠️ {symbol} tarama hatası: {e}")
            return None

    def scan_all(self) -> list[dict]:
        """Tüm coinleri tara, sinyalleri topla ve en iyi adayları göster"""
        self.refresh_symbols()
        signals = []
        all_candidates = []

        for i, symbol in enumerate(self.symbols):
            # Adayları toplamak için include_all=True kullanıyoruz
            signal = self.scan_symbol(symbol, include_all=True)
            if signal:
                all_candidates.append(signal)
                if signal.get('is_valid'):
                    signals.append(signal)

            # Rate limit koruması
            if (i + 1) % 15 == 0:
                time.sleep(0.3)

        # Tüm adayları skora göre sırala
        all_candidates.sort(key=lambda s: s['score'], reverse=True)
        
        # En iyi 5 adayı terminalde göster (Sinyal olmasa bile)
        logger.info("📋 --- EN İYİ 5 ADAY ---")
        for cand in all_candidates[:5]:
            status = "✅ GEÇERLİ" if cand['is_valid'] else f"🚫 {cand['filter_reason']}"
            fr = cand.get('funding_rate', 0)
            fr_icon = "🟢" if fr > 0.03 else ("🔴" if fr < -0.05 else "⚪")
            logger.info(f"🔹 {cand['symbol']}: Skor {cand['score']} | {status} | FR:{fr_icon}{fr*100:.3f}% | {', '.join(cand['reasons'][:3])}...")

        if signals:
            signals.sort(key=lambda s: s['score'], reverse=True)
            logger.info(f"🎯 {len(signals)} GEÇERLİ SİNYAL BULUNDU!")
        else:
            logger.info("🔍 Kriterlere uygun geçerli sinyal bulunamadı.")

        return signals
