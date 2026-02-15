import asyncio
import logging
import signal as sig
from datetime import datetime, timezone

# 🚀 uvloop kullan (daha hızlı async)
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print("🚀 uvloop aktif")
except ImportError:
    print("⚠️ uvloop yok, standart asyncio kullanılıyor")

from .config import (
    SCAN_INTERVAL_SECONDS, LOG_LEVEL, EXCHANGE_SANDBOX, TOP_COINS_COUNT
)
from .exchange import ExchangeClient
from .scanner import MarketScanner
from .portfolio import PortfolioManager
from .trader import TradeManager
from .redis_client import redis_client
from . import notifier
from .bybit_replay import BybitReplayProvider, ReplayExchangeClient

# Loglama
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(name)-10s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bot")


class CircuitBreaker:
    """🛡️ Circuit Breaker - Arka arkaya hatalarda duraklatma"""
    def __init__(self, threshold=5, timeout=300):
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure = 0
        self.is_open = False
    
    def can_execute(self):
        """İşlem yapılabilir mi?"""
        if self.is_open:
            if time.time() - self.last_failure > self.timeout:
                logger.info("🟢 Circuit Breaker kapandı, işlemler devam ediyor")
                self.is_open = False
                self.failures = 0
                return True
            return False
        return True
    
    def record_success(self):
        """Başarılı işlem - sayacı sıfırla"""
        if self.failures > 0:
            self.failures = 0
            logger.debug("Circuit Breaker sayacı sıfırlandı")
    
    def record_failure(self):
        """Başarısız işlem - sayacı artır"""
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.threshold:
            self.is_open = True
            logger.error(f"🔴 Circuit Breaker AÇIK! {self.timeout} saniye bekleniyor...")
            notifier.notify_error(f"Circuit Breaker: {self.failures} hata üst üste")

import time  # Circuit breaker için

# Graceful shutdown
_running = True
_is_replay_mode = False
_replay_provider = None
_circuit_breaker = CircuitBreaker(threshold=5, timeout=300)

# 🧠 Memory monitoring
def log_memory_usage():
    """Bellek kullanımını logla"""
    try:
        import psutil
        import gc
        process = psutil.Process()
        mem_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"🧠 Memory: {mem_mb:.1f} MB")
        if mem_mb > 500:  # 500MB threshold
            gc.collect()
            logger.warning("🧹 GC çalıştırıldı (yüksek bellek)")
    except ImportError:
        pass

def _shutdown(signum, frame):
    global _running
    logger.info("🛑 Kapatma sinyali alındı...")
    _running = False

async def main():
    """Ana giriş noktası"""
    global _running, _is_replay_mode, _replay_provider
    
    # Sinyal işleyici task'ı başlat
    signal_processor_task = asyncio.create_task(_signal_processor())
    
    # Sinyal yakalayıcıları
    try:
        loop = asyncio.get_running_loop()
        for s in (sig.SIGINT, sig.SIGTERM):
            loop.add_signal_handler(s, lambda: asyncio.create_task(_async_shutdown()))
    except NotImplementedError:
        sig.signal(sig.SIGINT, _shutdown)
        sig.signal(sig.SIGTERM, _shutdown)

    logger.info("=" * 60)
    logger.info("🤖 BUGRA-BOT v3.0.0")
    if EXCHANGE_SANDBOX:
        logger.info("   🧪 Paper Trading Mode")
    else:
        logger.info("   💰 Live Trading Mode")
    logger.info("   💡 Replay: POST /replay/start")
    logger.info("=" * 60)

    # Redis bağlantısı
    await redis_client.connect()

    # Başlangıç: Normal mod
    exchange = ExchangeClient()
    portfolio = PortfolioManager(exchange)
    scanner = MarketScanner(exchange)
    trade_manager = TradeManager(exchange, portfolio)

    # Bağlantı testi
    balance = portfolio.get_balance()
    if balance['total'] <= 0:
        logger.error("❌ Bakiye alınamadı. API key'leri kontrol edin.")
        return

    logger.info(f"💰 Bakiye: ${balance['total']:.2f}")
    
    last_daily_report = datetime.now(timezone.utc).hour
    cycle_count = 0

    # Ana döngü
    while _running:
        try:
            cycle_count += 1
            
            # API'den replay komutu kontrol et
            command = await redis_client.get("replay:command")
            if command:
                action = command.get("action")
                command_id = command.get("id", "unknown")
                
                try:
                    if action == "start" and not _is_replay_mode:
                        # Replay başlat
                        _replay_provider = await _start_replay(command.get("config", {}))
                        if _replay_provider:
                            exchange = ReplayExchangeClient(_replay_provider)
                            portfolio = PortfolioManager(exchange)
                            scanner = MarketScanner(exchange)
                            trade_manager = TradeManager(exchange, portfolio)
                            _is_replay_mode = True
                            logger.info("🎬 Replay başlatıldı!")
                            # Başarılı - state güncelle
                            await redis_client.set("replay:state", {
                                "status": "running",
                                "message": "Replay aktif"
                            })
                        else:
                            # Başarısız - hatayı kaydet
                            await redis_client.set("replay:state", {
                                "status": "error",
                                "message": "Replay başlatılamadı"
                            })
                        
                    elif action == "stop" and _is_replay_mode:
                        # Replay durdur
                        if _replay_provider:
                            _replay_provider.stop()
                        exchange = ExchangeClient()
                        portfolio = PortfolioManager(exchange)
                        scanner = MarketScanner(exchange)
                        trade_manager = TradeManager(exchange, portfolio)
                        _is_replay_mode = False
                        _replay_provider = None
                        logger.info("🛑 Replay durduruldu, canlı moda dönüldü")
                        await redis_client.set("replay:state", {
                            "status": "idle",
                            "message": "Replay durduruldu"
                        })
                    
                    elif action == "pause" and _is_replay_mode:
                        # Replay duraklat
                        if _replay_provider:
                            _replay_provider.stop()  # Zamanı durdur
                        logger.info("⏸️ Replay duraklatıldı")
                        await redis_client.set("replay:state", {
                            "status": "paused",
                            "message": "Replay duraklatıldı"
                        })
                    
                    elif action == "resume" and _is_replay_mode:
                        # Replay devam ettir
                        if _replay_provider:
                            _replay_provider.start()  # Zamanı ilerlet
                        logger.info("▶️ Replay devam ediyor")
                        await redis_client.set("replay:state", {
                            "status": "running",
                            "message": "Replay devam ediyor"
                        })
                    
                    # Başarılı işlem - komutu sil
                    await redis_client.delete("replay:command")
                    
                except Exception as e:
                    logger.error(f"❌ Komut işleme hatası ({action}): {e}")
                    await redis_client.set("replay:state", {
                        "status": "error",
                        "message": f"Komut hatası: {str(e)}"
                    })
                    # Hata durumunda komutu sil (tekrar denememesi için)
                    await redis_client.delete("replay:command")
            
            # Replay modu tick
            if _is_replay_mode and _replay_provider:
                continue_replay = await _replay_provider.tick(real_time_seconds=1.0)
                if not continue_replay:
                    logger.info("🎬 Replay tamamlandı!")
                    await redis_client.set("replay:state", {
                        "status": "completed",
                        "final_balance": portfolio.get_balance()['total']
                    })
                    # Canlı moda dön
                    exchange = ExchangeClient()
                    portfolio = PortfolioManager(exchange)
                    scanner = MarketScanner(exchange)
                    trade_manager = TradeManager(exchange, portfolio)
                    _is_replay_mode = False
                    _replay_provider = None
                    continue
                
                logger.info(f"\n🎬 Replay #{cycle_count} @ {_replay_provider.current_time}")
            else:
                logger.info(f"\n🔄 Döngü #{cycle_count}")

            # 0. Portföy Senkronizasyonu
            await portfolio.sync_positions()

            # 1. Açık pozisyonları kontrol et
            await trade_manager.check_positions(scanner=scanner)

            # 2. Piyasayı tara
            signals = await scanner.scan_all()

            # 3. Sinyalleri işle
            processed_symbols = set()
            for signal in signals:
                if not _running:
                    break
                
                if signal['symbol'] in processed_symbols:
                    continue
                processed_symbols.add(signal['symbol'])

                can_open, reason = portfolio.can_open_position(signal['symbol'])
                if can_open:
                    notifier.notify_signal(signal)
                    success = await trade_manager.execute_signal(signal)
                    if success:
                        await asyncio.sleep(1)

            # 4. Günlük özet
            if not _is_replay_mode:
                current_hour = datetime.now(timezone.utc).hour
                if current_hour == 0 and last_daily_report != 0:
                    stats = portfolio.get_stats()
                    notifier.notify_daily_summary(stats)
                    last_daily_report = 0
                elif current_hour != 0:
                    last_daily_report = current_hour

            # 5. Durum logu ve Redis güncelleme
            stats = portfolio.get_stats()
            stats['balance'] = portfolio.get_balance()['total']
            await redis_client.set("bot:stats", stats)
            
            # 🧠 Bellek kullanımını kontrol et (her 10 döngüde bir)
            if cycle_count % 10 == 0:
                log_memory_usage()
            
            # Replay durumunu güncelle
            if _is_replay_mode and _replay_provider:
                await redis_client.set("replay:state", {
                    "status": "running",
                    "current_time": _replay_provider.current_time.isoformat(),
                    "progress_pct": _replay_provider.get_progress(),
                    "balance": stats['balance'],
                    "open_positions": stats['open_positions']
                })
            
            logger.info(
                f"📊 Bakiye: ${stats['balance']:.2f} | "
                f"Açık: {stats['open_positions']} | "
                f"Günlük PnL: ${stats['daily_pnl']:+.2f}"
            )
            
            # Başarılı döngü - circuit breaker sıfırla
            _circuit_breaker.record_success()

            # Bekleme
            if _is_replay_mode:
                await asyncio.sleep(0.1)
            else:
                for _ in range(SCAN_INTERVAL_SECONDS):
                    if not _running:
                        break
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Döngü hatası: {e}", exc_info=True)
            _circuit_breaker.record_failure()
            
            if not _is_replay_mode:
                notifier.notify_error(str(e))
            
            # Circuit breaker açıksa daha uzun bekle
            if not _circuit_breaker.can_execute():
                logger.warning("⏳ Circuit Breaker aktif, 60 saniye bekleniyor...")
                await asyncio.sleep(60)
            else:
                await asyncio.sleep(30)

    # Kapatma
    logger.info("🛑 Bot kapatılıyor...")
    if _replay_provider:
        _replay_provider.stop()
    await redis_client.close()
    logger.info("👋 Güle güle!")


async def _signal_processor():
    """
    🚀 HEMEN SİNYAL İŞLEYİCİ
    Scanner'dan gelen sinyalleri hemen işleme alır (tarama bitmesini beklemez)
    """
    global _running, _is_replay_mode
    logger.info("🚀 Hemen sinyal işleyici başlatıldı")
    
    processed_signals = set()  # İşlenen sinyalleri takip et
    
    while _running:
        try:
            if _is_replay_mode:
                await asyncio.sleep(1)
                continue
            
            # Redis'ten hemen sinyalleri al
            # Tüm signal:immediate:* key'lerini bul
            keys = await redis_client._redis.keys("signal:immediate:*")
            
            for key in keys:
                try:
                    signal_data = await redis_client.get(key.replace("signal:immediate:", "signal:immediate:"))
                    if not signal_data:
                        continue
                    
                    symbol = signal_data['symbol']
                    signal_id = f"{symbol}:{signal_data['timestamp']}"
                    
                    # Daha önce işlendi mi?
                    if signal_id in processed_signals:
                        await redis_client._redis.delete(key)
                        continue
                    
                    # Sinyali hemen işle
                    logger.info(f"⚡ HEMEN İŞLENİYOR: {symbol} {signal_data['side']} @ {signal_data['entry_price']}")
                    
                    # Trade manager ile işle
                    from .trader import TradeManager
                    from .portfolio import PortfolioManager
                    
                    exchange = ExchangeClient()
                    portfolio = PortfolioManager(exchange)
                    trade_manager = TradeManager(exchange, portfolio)
                    
                    # Pozisyon aç
                    signal = {
                        'symbol': symbol,
                        'side': signal_data['side'],
                        'entry_price': signal_data['entry_price'],
                        'sl': signal_data['sl'],
                        'tp1': signal_data['tp1'],
                        'tp2': signal_data['tp2'],
                        'tp3': signal_data['tp3'],
                        'reason': signal_data.get('reason', ''),
                        'allocation': signal_data.get('allocation', 1.0)
                    }
                    
                    # Risk kontrolü
                    can_open, reason = portfolio.can_open_position(symbol)
                    if can_open:
                        success = await trade_manager.execute_signal(signal)
                        if success:
                            notifier.notify_signal(signal)
                            processed_signals.add(signal_id)
                            logger.info(f"✅ Hemen işlem tamamlandı: {symbol}")
                    else:
                        logger.warning(f"⏭️ Hemen işlem atlandı: {symbol} - {reason}")
                    
                    # Redis'ten sil
                    await redis_client._redis.delete(key)
                    
                except Exception as e:
                    logger.error(f"❌ Sinyal işleme hatası: {e}")
            
            # İşlenen sinyalleri temizle (çok eski olanları)
            current_time = time.time()
            processed_signals = {s for s in processed_signals if current_time - float(s.split(":")[1]) < 300}
            
            await asyncio.sleep(0.5)  # 500ms'de bir kontrol et
            
        except Exception as e:
            logger.error(f"❌ Signal processor hatası: {e}")
            await asyncio.sleep(1)

async def _start_replay(config: dict):
    """Replay başlat"""
    try:
        provider = BybitReplayProvider(speed_multiplier=config.get('speed', 100))
        
        start_dt = datetime.strptime(config['start_date'], "%Y-%m-%d")
        end_dt = datetime.strptime(config['end_date'], "%Y-%m-%d")
        
        symbols = config.get('symbols', [])
        top_coins = config.get('top_coins', 0)
        
        await provider.initialize(
            symbols=symbols,
            start_date=start_dt,
            end_date=end_dt,
            speed=config.get('speed', 100),
            top_coins=top_coins
        )
        
        provider.start()
        return provider
        
    except Exception as e:
        logger.error(f"❌ Replay başlatma hatası: {e}")
        return None


async def _async_shutdown():
    global _running
    logger.info("🛑 Kapatma sinyali alındı...")
    _running = False

if __name__ == "__main__":
    asyncio.run(main())
