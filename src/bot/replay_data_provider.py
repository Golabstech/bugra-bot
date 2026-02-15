"""
📼 REPLAY MODE - Canlı Veri Simülasyonu
backtest_data CSV dosyalarını hızlandırılmış canlı veri akışı gibi sunar
"""
import pandas as pd
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import asyncio

logger = logging.getLogger("replay")


class ReplayDataProvider:
    """
    CSV backtest verisini canlı veri akışı gibi sunar.
    
    Özellikler:
    - Tarih aralığı seçimi
    - Hızlandırılmış oynatma (1x, 10x, 100x, 1000x)
    - Gerçek zamanlı sinyal üretimi için uygun
    - MTF (Multi-Timeframe) desteği
    """
    
    def __init__(self, data_folder: str = "backtest_data", speed_multiplier: float = 100.0):
        self.data_folder = Path(data_folder)
        self.speed_multiplier = speed_multiplier
        self.current_time: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.data_cache: dict[str, pd.DataFrame] = {}
        self.symbols: list[str] = []
        self._running = False
        
    def load_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Belirli bir coin için tarih aralığındaki veriyi yükle
        """
        # CSV dosyasını bul - farklı formatları dene
        # Symbol: "BTCUSDT" -> dosya: "BTC_USDT_USDT.csv"
        base_symbol = symbol.replace('USDT', '')
        possible_files = [
            self.data_folder / f"{base_symbol}_USDT_USDT.csv",
            self.data_folder / f"{symbol}_USDT_USDT.csv",
            self.data_folder / f"{base_symbol}USDT_USDT.csv",
        ]
        
        csv_file = None
        for pf in possible_files:
            if pf.exists():
                csv_file = pf
                break
        
        if not csv_file:
            logger.debug(f"📵 {symbol} için veri dosyası bulunamadı (normal, tüm coinler olmayabilir)")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Tarih filtresi uygula
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
            
            logger.info(f"📊 {symbol}: {len(df)} mum yüklendi ({start_date} - {end_date})")
            return df
            
        except Exception as e:
            logger.error(f"❌ {symbol} veri yükleme hatası: {e}")
            return pd.DataFrame()
    
    def initialize_replay(self, symbols: list[str], start_date: datetime, 
                          end_date: datetime, speed: float = 100.0):
        """
        Replay modunu başlat
        
        Args:
            symbols: İzlenecek coinler
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi
            speed: Hız çarpanı (1.0 = gerçek zaman, 100.0 = 100x hızlı)
        """
        self.symbols = symbols
        self.current_time = start_date
        self.start_time = start_date
        self.end_time = end_date
        self.speed_multiplier = speed
        self.data_cache = {}
        
        # Tüm coinlerin verisini yükle
        for symbol in symbols:
            df = self.load_data(symbol, start_date, end_date)
            if not df.empty:
                self.data_cache[symbol] = df
        
        if not self.data_cache:
            raise ValueError("Hiçbir coin verisi yüklenemedi!")
        
        logger.info(f"🎬 REPLAY MODU HAZIR")
        logger.info(f"   📅 Tarih: {start_date} → {end_date}")
        logger.info(f"   🚀 Hız: {speed}x")
        logger.info(f"   📊 Coinler: {len(self.data_cache)}")
    
    def start(self):
        """Replay'ı başlat"""
        self._running = True
        logger.info("▶️ Replay başlatıldı")
    
    def stop(self):
        """Replay'ı durdur"""
        self._running = False
        logger.info("⏹️ Replay durduruldu")
    
    def get_progress(self) -> float:
        """İlerleme yüzdesini döndür (0-100)"""
        if not self.current_time or not self.end_time:
            return 0.0
        total = (self.end_time - self.start_time).total_seconds()
        current = (self.current_time - self.start_time).total_seconds()
        if total <= 0:
            return 100.0
        return min(100.0, (current / total) * 100)
        
    def get_current_data(self, symbol: str, lookback: int = 50) -> pd.DataFrame:
        """
        Mevcut replay zamanına kadar olan veriyi getir (canlı veri simülasyonu)
        
        Args:
            symbol: Coin sembolü
            lookback: Kaç mum geriye bakılacağı
            
        Returns:
            DataFrame: OHLCV verisi
        """
        if symbol not in self.data_cache:
            return pd.DataFrame()
        
        df = self.data_cache[symbol]
        # Mevcut zamana kadar olan veriyi filtrele
        mask = df['timestamp'] <= self.current_time
        available_data = df[mask]
        
        if len(available_data) < lookback:
            return available_data  # Yetersiz veri
        
        return available_data.tail(lookback)
    
    def get_current_ticker(self, symbol: str) -> Optional[dict]:
        """
        Mevcut replay zamanındaki son fiyatı getir
        """
        df = self.get_current_data(symbol, lookback=1)
        if df.empty:
            return None
        
        last = df.iloc[-1]
        return {
            'symbol': symbol,
            'last': float(last['close']),
            'bid': float(last['close']) * 0.9999,
            'ask': float(last['close']) * 1.0001,
            'timestamp': self.current_time.isoformat()
        }
    
    async def tick(self, real_time_seconds: float = 1.0) -> bool:
        """
        Replay zamanını ilerlet
        
        Args:
            real_time_seconds: Gerçek zaman kaç saniye beklenecek
            
        Returns:
            bool: Replay devam ediyor mu?
        """
        if not self._running or self.current_time >= self.end_time:
            return False
        
        # Hızlandırılmış zaman ilerlemesi
        # Örneğin: 100x hızda, 1 saniye = 100 saniye replay zamanı
        time_step = timedelta(seconds=real_time_seconds * self.speed_multiplier)
        self.current_time += time_step
        
        # Veri sonuna gelindi mi?
        if self.current_time > self.end_time:
            self.current_time = self.end_time
            return False
        
        return True
    
    def start(self):
        """Replay'ı başlat"""
        self._running = True
        logger.info(f"▶️ REPLAY BAŞLADI @ {self.current_time}")
    
    def stop(self):
        """Replay'ı durdur"""
        self._running = False
        logger.info(f"⏹️ REPLAY DURDURULDU @ {self.current_time}")
    
    def is_running(self) -> bool:
        """Replay çalışıyor mu?"""
        return self._running and self.current_time < self.end_time
    
    def get_progress(self) -> float:
        """Replay ilerleme yüzdesi"""
        if not self.end_time or not self.current_time:
            return 0.0
        total = (self.end_time - self.current_time).total_seconds()
        return min(100.0, max(0.0, 100.0 - (total / (self.end_time - self.current_time).total_seconds() * 100)))


class ReplayExchangeClient:
    """
    Gerçek ExchangeClient yerine kullanılan replay versiyonu.
    Tüm işlemler simüle edilir, gerçek borsaya bağlanılmaz.
    """
    
    def __init__(self, data_provider: ReplayDataProvider):
        self.data_provider = data_provider
        self.simulated_positions: dict = {}
        self.simulated_orders: list = []
        self.balance = {'total': 10000.0, 'free': 10000.0, 'used': 0.0}
        
    def fetch_ticker(self, symbol: str) -> Optional[dict]:
        """Replay verisinden ticker getir"""
        return self.data_provider.get_current_ticker(symbol)
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> list:
        """Replay verisinden OHLCV getir"""
        df = self.data_provider.get_current_data(symbol, lookback=limit)
        if df.empty:
            return []
        
        # CCXT formatına çevir: [timestamp, open, high, low, close, volume]
        ohlcv = []
        for _, row in df.iterrows():
            ohlcv.append([
                int(row['timestamp'].timestamp() * 1000),
                float(row['open']),
                float(row['high']),
                float(row['low']),
                float(row['close']),
                float(row['volume'])
            ])
        return ohlcv
    
    def get_balance(self) -> dict:
        """Simüle edilmiş bakiye"""
        return self.balance
    
    def get_positions(self) -> list:
        """Simüle edilmiş pozisyonlar"""
        return list(self.simulated_positions.values())
    
    def open_long(self, symbol: str, amount: float) -> dict:
        """Simüle edilmiş LONG açma"""
        ticker = self.fetch_ticker(symbol)
        if not ticker:
            return None
        
        price = ticker['last']
        self.simulated_positions[symbol] = {
            'symbol': symbol,
            'side': 'LONG',
            'contracts': amount,
            'entryPrice': price,
            'markPrice': price,
            'unrealizedPnl': 0.0
        }
        
        logger.info(f"📈 [REPLAY] LONG AÇILDI: {symbol} @ {price} | Miktar: {amount}")
        return {'id': f'replay_{symbol}_long', 'average': price}
    
    def open_short(self, symbol: str, amount: float) -> dict:
        """Simüle edilmiş SHORT açma"""
        ticker = self.fetch_ticker(symbol)
        if not ticker:
            return None
        
        price = ticker['last']
        self.simulated_positions[symbol] = {
            'symbol': symbol,
            'side': 'SHORT',
            'contracts': amount,
            'entryPrice': price,
            'markPrice': price,
            'unrealizedPnl': 0.0
        }
        
        logger.info(f"📉 [REPLAY] SHORT AÇILDI: {symbol} @ {price} | Miktar: {amount}")
        return {'id': f'replay_{symbol}_short', 'average': price}
    
    def close_position(self, symbol: str, side: str, amount: float) -> dict:
        """Simüle edilmiş pozisyon kapatma"""
        if symbol in self.simulated_positions:
            del self.simulated_positions[symbol]
            logger.info(f"✅ [REPLAY] POZİSYON KAPATILDI: {symbol}")
        return {'id': f'replay_close_{symbol}'}
    
    def set_stop_loss(self, symbol: str, side: str, stop_price: float) -> dict:
        """Simüle edilmiş SL ayarlama (replay'de sadece log)"""
        logger.debug(f"🛑 [REPLAY] SL Ayarlandı: {symbol} @ {stop_price}")
        return {'id': f'replay_sl_{symbol}'}
    
    def cancel_all_orders(self, symbol: str):
        """Simüle edilmiş emir iptali"""
        pass
    
    def set_leverage(self, symbol: str, leverage: int):
        """Simüle edilmiş kaldıraç ayarı"""
        pass
    
    def set_margin_mode(self, symbol: str, mode: str = "isolated"):
        """Simüle edilmiş margin modu"""
        pass
