"""
📼 BYBIT REPLAY MODE - API Tabanlı Basit Replay
Gerçek Bybit API'den geçmiş veri çekerek replay yapar
"""
import ccxt
import pandas as pd
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import asyncio
from .redis_client import redis_client

logger = logging.getLogger("replay")


class BybitReplayProvider:
    """
    Bybit API'den geçmiş veri çekerek replay yapar.
    Redis cache + paralel fetching ile hızlı başlangıç.
    """
    
    def __init__(self, speed_multiplier: float = 100.0):
        self.speed_multiplier = speed_multiplier
        self.current_time: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.data_cache: dict[str, pd.DataFrame] = {}
        self.symbols: list[str] = []
        self._running = False
        
        # Bybit bağlantısı (public - API key gerekmez)
        self.exchange = ccxt.bybit({
            'enableRateLimit': True,
            'options': {'defaultType': 'linear'}
        })
        
    def _get_cache_key(self, symbol: str, start: datetime, end: datetime) -> str:
        """Cache key oluştur: symbol + tarih aralığı"""
        key_data = f"{symbol}:{start.isoformat()}:{end.isoformat()}"
        return f"replay:cache:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def _get_cached_data(self, symbol: str, start: datetime, end: datetime) -> Optional[pd.DataFrame]:
        """Redis'ten cache'lenmiş veriyi al"""
        try:
            cache_key = self._get_cache_key(symbol, start, end)
            cached = await redis_client.get(cache_key)
            
            if cached and 'data' in cached:
                # JSON'dan DataFrame'e çevir
                df_data = json.loads(cached['data'])
                df = pd.DataFrame(df_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                logger.info(f"💾 {symbol}: Cache'den yüklendi ({len(df)} mum)")
                return df
        except Exception as e:
            logger.debug(f"Cache okuma hatası {symbol}: {e}")
        return None
    
    async def _cache_data(self, symbol: str, start: datetime, end: datetime, df: pd.DataFrame):
        """Veriyi Redis'e cachele"""
        try:
            cache_key = self._get_cache_key(symbol, start, end)
            # DataFrame'i JSON'a çevir
            df_copy = df.copy()
            df_copy['timestamp'] = df_copy['timestamp'].astype(str)
            cache_data = {
                'symbol': symbol,
                'start': start.isoformat(),
                'end': end.isoformat(),
                'data': df_copy.to_json(orient='records'),
                'cached_at': datetime.now().isoformat()
            }
            # 7 gün cache'de tut
            await redis_client.set(cache_key, cache_data, expire=604800)
            logger.debug(f"💾 {symbol}: Cache'lendi")
        except Exception as e:
            logger.debug(f"Cache yazma hatası {symbol}: {e}")
        
    async def initialize(self, symbols: list[str], start_date: datetime, 
                         end_date: datetime, speed: float = 100.0,
                         top_coins: int = 0):
        """
        Replay'i başlat - veriyi API'den çek
        
        Args:
            symbols: İzlenecek coinler (top_coins=0 ise kullanılır)
            start_date: Başlangıç tarihi
            end_date: Bitiş tarihi  
            speed: Hız çarpanı
            top_coins: Otomatik coin sayısı (50/100/200), 0=symbols kullan
        """
        # Top coins modu - Bybit'ten çek
        logger.info(f"🔧 Initialize: top_coins={top_coins}, symbols={len(symbols)}")
        
        if top_coins > 0:
            logger.info(f"🏆 Top {top_coins} coin çekiliyor...")
            self.symbols = await self._fetch_top_coins(top_coins)
            logger.info(f"📊 Bybit'ten {len(self.symbols)} coin çekildi")
        else:
            self.symbols = symbols
            logger.info(f"📊 Manuel {len(self.symbols)} coin kullanılıyor")
            
        self.start_time = start_date
        self.end_time = end_date
        self.current_time = start_date
        self.speed_multiplier = speed
        
        logger.info(f"📼 Bybit Replay Başlatılıyor...")
        logger.info(f"   📅 {start_date} → {end_date}")
        logger.info(f"   🚀 {speed}x hız")
        logger.info(f"   📊 {len(self.symbols)} coin")
        
        # Önce cache kontrolü yap, eksik coinleri belirle
        cached_count = 0
        fetch_symbols = []
        
        for symbol in self.symbols:
            cached_df = await self._get_cached_data(symbol, start_date, end_date)
            if cached_df is not None:
                self.data_cache[symbol] = cached_df
                cached_count += 1
            else:
                fetch_symbols.append(symbol)
        
        if cached_count > 0:
            logger.info(f"💾 {cached_count} coin cache'den yüklendi")
        
        # Eksik coinleri paralel çek
        if fetch_symbols:
            logger.info(f"🌐 {len(fetch_symbols)} coin API'den çekiliyor (paralel)...")
            await self._fetch_all_history_parallel(fetch_symbols, start_date, end_date)
        
        if not self.data_cache:
            raise ValueError("Hiçbir coin verisi çekilemedi!")
        
        logger.info(f"✅ Replay hazır: {len(self.data_cache)} coin yüklendi")
    
    async def _fetch_all_history_parallel(self, symbols: list[str], start: datetime, end: datetime):
        """
        Tüm coinleri paralel olarak çek - hızlı başlangıç için
        """
        semaphore = asyncio.Semaphore(5)  # Aynı anda max 5 istek
        
        async def fetch_with_limit(symbol: str):
            async with semaphore:
                df = await self._fetch_history(symbol, start, end)
                if not df.empty:
                    self.data_cache[symbol] = df
                    # Cache'e kaydet
                    await self._cache_data(symbol, start, end, df)
                await asyncio.sleep(0.1)  # Kısa bekleme
        
        # Tüm coinleri paralel başlat
        tasks = [fetch_with_limit(sym) for sym in symbols]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_top_coins(self, count: int = 50) -> list[str]:
        """
        Bybit'ten hacme göre top coinleri çek
        """
        try:
            # Bybit tickers çek (async olarak)
            tickers = await asyncio.to_thread(self.exchange.fetch_tickers)
            
            # USDT futures filtrele ve hacme göre sırala
            futures = []
            for symbol, ticker in tickers.items():
                # CCXT format: BTC/USDT:USDT (linear futures)
                if ':USDT' in symbol and ticker.get('quoteVolume'):
                    futures.append({
                        'symbol': symbol.replace('/USDT:USDT', 'USDT'),
                        'volume': float(ticker.get('quoteVolume', 0))
                    })
            
            # Hacme göre sırala
            futures.sort(key=lambda x: x['volume'], reverse=True)
            
            # İlk N coini al
            top_symbols = [f['symbol'] for f in futures[:count]]
            
            logger.info(f"🏆 Top {len(top_symbols)} coin: {', '.join(top_symbols[:5])}...")
            return top_symbols
            
        except Exception as e:
            logger.error(f"❌ Top coinler çekilemedi: {e}")
            # Fallback: popüler coinler
            return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT'][:count]
        
    async def _fetch_history(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """
        Bybit'ten geçmiş OHLCV verisi çek
        """
        try:
            # CCXT formatına çevir: BTCUSDT -> BTC/USDT:USDT
            if '/' not in symbol:
                ccxt_symbol = f"{symbol.replace('USDT', '')}/USDT:USDT"
            else:
                ccxt_symbol = symbol
                
            since = int(start.timestamp() * 1000)
            
            # Veriyi çek (pagination ile)
            all_ohlcv = []
            current_since = since
            
            while True:
                ohlcv = self.exchange.fetch_ohlcv(
                    ccxt_symbol, 
                    timeframe='15m',  # 15m varsayılan
                    since=current_since,
                    limit=1000
                )
                
                if not ohlcv:
                    break
                    
                all_ohlcv.extend(ohlcv)
                
                # Sonraki batch
                current_since = ohlcv[-1][0] + 1
                
                # Bitiş tarihini geçtik mi?
                if current_since > int(end.timestamp() * 1000):
                    break
                    
                await asyncio.sleep(0.2)  # Rate limit
            
            if not all_ohlcv:
                logger.warning(f"⚠️ {symbol}: Veri alınamadı")
                return pd.DataFrame()
            
            # DataFrame oluştur
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Tarih filtresi
            df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
            
            logger.info(f"📊 {symbol}: {len(df)} mum yüklendi")
            return df
            
        except Exception as e:
            logger.error(f"❌ {symbol} veri hatası: {e}")
            return pd.DataFrame()
    
    def start(self):
        """Replay'i başlat"""
        self._running = True
        logger.info(f"▶️ Replay başlatıldı @ {self.current_time}")
    
    def stop(self):
        """Replay'i durdur"""
        self._running = False
        logger.info(f"⏹️ Replay durduruldu @ {self.current_time}")
    
    def is_running(self) -> bool:
        """Replay çalışıyor mu?"""
        return self._running and self.current_time < self.end_time
    
    def get_progress(self) -> float:
        """İlerleme yüzdesi (0-100)"""
        if not self.current_time or not self.end_time:
            return 0.0
        total = (self.end_time - self.start_time).total_seconds()
        current = (self.current_time - self.start_time).total_seconds()
        if total <= 0:
            return 100.0
        return min(100.0, (current / total) * 100)
    
    def get_current_data(self, symbol: str, lookback: int = 50) -> pd.DataFrame:
        """
        Mevcut replay zamanına kadar olan veriyi getir
        """
        if symbol not in self.data_cache:
            return pd.DataFrame()
        
        df = self.data_cache[symbol]
        mask = df['timestamp'] <= self.current_time
        available = df[mask]
        
        if len(available) < lookback:
            return available
        
        return available.tail(lookback)
    
    def get_current_ticker(self, symbol: str) -> Optional[dict]:
        """Mevcut zamandaki son fiyat"""
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
        
        Returns:
            bool: Replay devam ediyor mu?
        """
        if not self._running or self.current_time >= self.end_time:
            return False
        
        # Hızlandırılmış zaman
        time_step = timedelta(seconds=real_time_seconds * self.speed_multiplier)
        self.current_time += time_step
        
        if self.current_time > self.end_time:
            self.current_time = self.end_time
            return False
        
        return True


class ReplayExchangeClient:
    """
    Replay için simüle edilmiş exchange client
    """
    
    def __init__(self, data_provider: BybitReplayProvider):
        self.data_provider = data_provider
        self.simulated_positions: dict = {}
        self.balance = {'total': 10000.0, 'free': 10000.0, 'used': 0.0}
        
    def fetch_ticker(self, symbol: str) -> Optional[dict]:
        return self.data_provider.get_current_ticker(symbol)
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> list:
        df = self.data_provider.get_current_data(symbol, lookback=limit)
        if df.empty:
            return []
        
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
        return self.balance
    
    def get_positions(self) -> list:
        return list(self.simulated_positions.values())
    
    def open_long(self, symbol: str, amount: float) -> dict:
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
        
        logger.info(f"📈 [REPLAY] LONG: {symbol} @ {price} | {amount}")
        return {'id': f'replay_{symbol}_long', 'average': price}
    
    def open_short(self, symbol: str, amount: float) -> dict:
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
        
        logger.info(f"📉 [REPLAY] SHORT: {symbol} @ {price} | {amount}")
        return {'id': f'replay_{symbol}_short', 'average': price}
    
    def close_position(self, symbol: str, side: str, amount: float) -> dict:
        if symbol in self.simulated_positions:
            del self.simulated_positions[symbol]
            logger.info(f"✅ [REPLAY] KAPATILDI: {symbol}")
        return {'id': f'replay_close_{symbol}'}
    
    def set_stop_loss(self, symbol: str, side: str, stop_price: float) -> dict:
        logger.debug(f"🛑 [REPLAY] SL: {symbol} @ {stop_price}")
        return {'id': f'replay_sl_{symbol}'}
    
    def cancel_all_orders(self, symbol: str):
        pass
    
    def cleanup_orphan_orders(self, active_symbols: set):
        """Replay modunda yetim emir temizliği (no-op)"""
        pass
    
    def set_leverage(self, symbol: str, leverage: int):
        pass
    
    def set_margin_mode(self, symbol: str, mode: str = "isolated"):
        pass
    
    def sanitize_amount(self, symbol: str, amount: float) -> float:
        """Miktarı market limitlerine uygun hale getir (simüle edilmiş)"""
        # Replay modunda basit bir doğrulama yap
        if amount <= 0:
            return 0.0
        # Minimum 0.001, maksimum 1M limit
        return max(0.001, min(amount, 1000000))
    
    # Scanner compatibility - internal exchange object simulation
    @property
    def exchange(self):
        """Scanner compatibility - returns self for exchange.exchange access"""
        return self
    
    def fapiPublicGetTicker24hr(self) -> list:
        """Scanner compatibility - returns simulated tickers for replay symbols"""
        tickers = []
        for symbol in self.data_provider.symbols:
            ticker = self.fetch_ticker(symbol)
            if ticker:
                # Binance formatına benzer yapı
                tickers.append({
                    'symbol': symbol,
                    'lastPrice': str(ticker['last']),
                    'quoteVolume': '1000000',  # Simulated
                    'volume': '10000'
                })
        return tickers
    
    @property
    def markets(self) -> dict:
        """Scanner compatibility - returns simulated markets"""
        markets = {}
        for symbol in self.data_provider.symbols:
            markets[symbol] = {
                'symbol': symbol,
                'active': True,
                'limits': {
                    'amount': {'min': 0.001, 'max': 1000000}
                }
            }
        return markets
    
    def load_markets(self, reload: bool = False):
        """Scanner compatibility - no-op"""
        pass
