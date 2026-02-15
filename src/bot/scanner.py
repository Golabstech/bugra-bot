"""
🔍 Market Tarayıcı
Top 100 coin'i sürekli tarar, strateji sinyallerini üretir
"""
import pandas as pd
import logging
import time
import asyncio
from .exchange import ExchangeClient
from .strategy import Strategy, PendingSignal
from .config import (
    TIMEFRAME, OHLCV_LIMIT, TOP_COINS_COUNT, MIN_24H_VOLUME,
    MTF_ENABLED, MTF_TIMEFRAME, PULLBACK_ENABLED
)

from .redis_client import redis_client

logger = logging.getLogger("scanner")


class MarketScanner:
    """Sürekli çalışan piyasa tarayıcı v2.0 - MTF + Pullback"""

    def __init__(self, exchange: ExchangeClient):
        self.exchange = exchange
        self.strategy = Strategy()
        self.symbols: list[str] = []
        
        # 🎯 Pullback bekleyen sinyaller
        self.pending_signals: dict[str, PendingSignal] = {}
        
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
            
            # 3. Hacim Kontrolü (Minimum 24s hacim)
            quote_vol = float(t.get('quoteVolume', 0))
            if quote_vol < MIN_24H_VOLUME: 
                continue
            
            # 4. Status Kontrolü (Sadece aktif işlem görenleri al)
            # Not: Ticker verisinden status gelmeyebilir, exchange.markets'tan doğrulanabilir
            if not self.exchange.exchange.markets:
                self.exchange.exchange.load_markets(reload=True)
            
            market_info = self.exchange.exchange.markets.get(symbol)
            if market_info:
                # Hem active bayrağını hem de Binance'in status (TRADING) değerini kontrol et
                active = market_info.get('active', True)
                status = market_info.get('info', {}).get('status', 'TRADING')
                
                if not active or status != 'TRADING':
                    continue
            
            top_coins.append(symbol)
            if len(top_coins) >= limit:
                break
        
        self.symbols = top_coins
        self.last_refresh = now
        logger.info(f"✅ {len(self.symbols)} coin yüklendi (Filtrelendi)")

    async def scan_symbol(self, symbol: str) -> dict | None:
        """Tek bir coin'i tara ve sinyal üret"""
        try:
            # Ana timeframe verisi
            ohlcv = self.exchange.fetch_ohlcv(symbol, TIMEFRAME, OHLCV_LIMIT)
            if not ohlcv or len(ohlcv) < 20:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = self.strategy.calculate_indicators(df)
            
            # 🔄 MTF verisi (Özellik aktifse)
            df_mtf = None
            if MTF_ENABLED:
                ohlcv_mtf = self.exchange.fetch_ohlcv(symbol, MTF_TIMEFRAME, 50)
                if ohlcv_mtf and len(ohlcv_mtf) >= 25:
                    df_mtf = pd.DataFrame(ohlcv_mtf, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Sinyal üret (MTF dahil)
            signal = self.strategy.generate_signal(symbol, df, df_mtf)
            
            if signal.get('side') not in ['WAIT', None]:
                return signal
            
            return None

        except Exception as e:
            logger.debug(f"⚠️ {symbol} tarama hatası: {e}")
            return None
    
    async def check_pending_pullbacks(self) -> list[dict]:
        """
        🎯 Bekleyen pullback sinyallerini kontrol et
        Her Fibonacci seviyesine ulaşıldığında kademeli pozisyon açılır
        """
        triggered_signals = []
        symbols_to_remove = []
        
        for symbol, pending in self.pending_signals.items():
            try:
                # Güncel fiyatı al
                ticker = self.exchange.fetch_ticker(symbol)
                if not ticker:
                    continue
                
                current_price = float(ticker['last'])
                
                # Pullback durumunu kontrol et
                result = self.strategy.process_pullback(pending, current_price)
                side = result.get('side', 'WAITING')
                
                if side == 'TIERED_ENTRY':
                    # Yeni seviye tetiklendi, kademeli pozisyon sinyali
                    allocation = result.get('total_allocated', 0)
                    signal = self.strategy._build_tiered_signal(
                        symbol=symbol,
                        side_type=result['side_type'],
                        entry_price=result['entry_price'],
                        atr=result['atr'],
                        reason=result['reason'],
                        allocation=allocation
                    )
                    triggered_signals.append(signal)
                    
                    # Tüm pozisyon açıldıysa pending'i temizle
                    if pending.fully_triggered:
                        symbols_to_remove.append(symbol)
                        logger.info(f"✅ {symbol} FULL POSITION OPENED @ {current_price} | Toplam: {allocation:.0%}")
                    else:
                        logger.info(f"✅ {symbol} TIER #{len(pending.triggered_levels)} @ {current_price} | Bu: {allocation:.0%}")
                
                elif side == 'CANCELLED':
                    # Pullback iptal edildi
                    symbols_to_remove.append(symbol)
                    total_allocated = result.get('total_allocated', 0)
                    if total_allocated > 0:
                        logger.info(f"❌ {symbol} PULLBACK CANCELLED (kısmi açıldı: {total_allocated:.0%})")
                    else:
                        logger.info(f"❌ {symbol} PULLBACK CANCELLED (hiç açılmadı)")
                
                # 'WAITING' durumunda devam et
                
            except Exception as e:
                logger.debug(f"⚠️ {symbol} pullback kontrol hatası: {e}")
        
        # Tamamlanan/iptal edilen sinyalleri temizle
        for sym in symbols_to_remove:
            if sym in self.pending_signals:
                del self.pending_signals[sym]
        
        return triggered_signals

    async def scan_all(self) -> list[dict]:
        """Tüm coinleri paralel tara ve aktif sinyalleri dön"""
        self.refresh_symbols()
        
        logger.info(f"🔍 {len(self.symbols)} parite momentum için taranıyor...")
        
        # 🎯 ÖNCE: Bekleyen pullback'leri kontrol et
        pullback_signals = []
        if PULLBACK_ENABLED and self.pending_signals:
            logger.info(f"⏳ {len(self.pending_signals)} bekleyen pullback kontrol ediliyor...")
            pullback_signals = await self.check_pending_pullbacks()
        
        # Paralel tarama (Batch processing)
        tasks = [self.scan_symbol(sym) for sym in self.symbols]
        results = await asyncio.gather(*tasks)
        
        # Yeni sinyalleri işle
        new_signals = []
        for signal in results:
            if signal is None:
                continue
            
            # YENİ: Hemen giriş + Pullback kuyruğu yapısı
            pending = signal.get('pending_pullback')
            if pending and pending.symbol not in self.pending_signals:
                self.pending_signals[pending.symbol] = pending
                levels = [f"Fib{lvl*100:.0f}%" for lvl in sorted(pending.fib_levels)]
                logger.info(f"🎯 {pending.symbol} PULLBACK QUEUE | {' | '.join(levels)} | Timeout: {PULLBACK_TIMEOUT_CANDLES}m")
            
            # Direkt işleme hazır sinyal (hemen giriş kısmı)
            if signal.get('side') in ['LONG', 'SHORT']:
                new_signals.append(signal)
        
        # Pullback'ten gelen sinyalleri birleştir
        all_signals = pullback_signals + new_signals

        if all_signals:
            pullback_count = len([s for s in all_signals if s.get('allocation', 1.0) < 1.0])
            full_count = len(all_signals) - pullback_count
            logger.info(f"🎯 {len(all_signals)} SINYAL ({full_count} tam + {pullback_count} kademeli)")
            for sig in all_signals:
                alloc_info = f" [{sig.get('allocation', 1.0):.0%}]" if sig.get('allocation') else ""
                logger.info(f"✅ {sig['symbol']}: {sig['side']}{alloc_info} | {sig.get('reason', '')}")
        else:
            pending_count = len(self.pending_signals)
            if pending_count > 0:
                logger.info(f"🔍 Aktif sinyal yok. ⏳ {pending_count} pullback bekliyor.")
            else:
                logger.info("🔍 Kriterlere uygun momentum hareketi bulunamadı.")

        return all_signals
