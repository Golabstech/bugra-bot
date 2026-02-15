import asyncio
import logging
import signal as sig
from datetime import datetime, timezone, timedelta

from .config import (
    SCAN_INTERVAL_SECONDS, LOG_LEVEL,
    REPLAY_MODE, REPLAY_SPEED, REPLAY_START_DATE, REPLAY_END_DATE,
    REPLAY_DATA_FOLDER, TOP_COINS_COUNT
)
from .exchange import ExchangeClient
from .scanner import MarketScanner
from .portfolio import PortfolioManager
from .trader import TradeManager
from .redis_client import redis_client
from . import notifier

# Replay modu için
if REPLAY_MODE:
    from .replay_data_provider import ReplayDataProvider, ReplayExchangeClient

# Loglama
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(name)-10s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bot")

# Graceful shutdown
_running = True

# Replay modu değişkenleri
_replay_provider = None

def _shutdown(signum, frame):
    global _running
    logger.info("🛑 Kapatma sinyali alındı...")
    _running = False
    if _replay_provider:
        _replay_provider.stop()

async def main():
    """Ana giriş noktası (Async) - API Kontrollü Replay Desteği"""
    global _running, _replay_provider
    
    # Sinyal yakalayıcıları (Unix/Windows uyumlu)
    try:
        loop = asyncio.get_running_loop()
        for s in (sig.SIGINT, sig.SIGTERM):
            loop.add_signal_handler(s, lambda: asyncio.create_task(_async_shutdown()))
    except NotImplementedError:
        # Windows'ta loop.add_signal_handler yok
        sig.signal(sig.SIGINT, _shutdown)
        sig.signal(sig.SIGTERM, _shutdown)

    logger.info("=" * 60)
    if REPLAY_MODE:
        logger.info("🎬 BUGRA-BOT v3.0.0 — REPLAY MODE (ENV)")
        logger.info(f"   📅 {REPLAY_START_DATE} → {REPLAY_END_DATE}")
        logger.info(f"   🚀 {REPLAY_SPEED}x HIZLANDIRILMIŞ")
    else:
        logger.info("🤖 BUGRA-BOT v3.0.0 — Northflank Ready Engine")
        logger.info("   💡 API'den replay başlatabilirsiniz: POST /replay/start")
    logger.info("=" * 60)

    # Redis bağlantısını başlat
    await redis_client.connect()

    # Başlangıçta canlı modda başla
    exchange = ExchangeClient()
    portfolio = PortfolioManager(exchange)
    scanner = MarketScanner(exchange)
    trade_manager = TradeManager(exchange, portfolio)

    # Bağlantı testi (sadece canlı modda)
    if not REPLAY_MODE:
        balance = portfolio.get_balance()
        if balance['total'] <= 0:
            logger.error("❌ Bakiye alınamadı veya sıfır. API key'leri kontrol edin.")
            notifier.notify_error("Bakiye alınamadı! API key kontrol edin.")
            return

        logger.info(f"💰 Bakiye: ${balance['total']:.2f} (Free: ${balance['free']:.2f})")
        notifier.send(
            f"🚀 <b>Bot Başlatıldı (Northflank Mode)</b>\n"
            f"💰 Bakiye: ${balance['total']:.2f}\n"
            f"⏱️ Tarama: her {SCAN_INTERVAL_SECONDS}s"
        )
    else:
        logger.info(f"💰 Simüle Bakiye: $10,000")

    last_daily_report = datetime.now(timezone.utc).hour if not REPLAY_MODE else 0
    cycle_count = 0
    
    # Replay durumu
    is_replay_mode = REPLAY_MODE
    replay_provider = None
    
    if REPLAY_MODE:
        # ENV'den replay başlat
        replay_provider = await _init_replay_from_env()
        if replay_provider:
            exchange = ReplayExchangeClient(replay_provider)
            portfolio = PortfolioManager(exchange)
            scanner = MarketScanner(exchange)
            trade_manager = TradeManager(exchange, portfolio)
            is_replay_mode = True
            replay_provider.start()

    # Ana döngü
    while _running:
        try:
            cycle_count += 1
            
            # API'den replay komutu var mı kontrol et
            if not REPLAY_MODE:  # Canlı moddayken API kontrolü
                command = await redis_client.get("replay:command")
                if command:
                    action = command.get("action")
                    if action == "start" and not is_replay_mode:
                        # Replay başlat
                        config = command.get("config", {})
                        replay_provider = await _init_replay_from_api(config)
                        if replay_provider:
                            exchange = ReplayExchangeClient(replay_provider)
                            portfolio = PortfolioManager(exchange)
                            scanner = MarketScanner(exchange)
                            trade_manager = TradeManager(exchange, portfolio)
                            is_replay_mode = True
                            replay_provider.start()
                            logger.info("🎬 API'den replay başlatıldı!")
                    elif action == "stop" and is_replay_mode:
                        # Replay durdur, canlı moda dön
                        if replay_provider:
                            replay_provider.stop()
                        exchange = ExchangeClient()
                        portfolio = PortfolioManager(exchange)
                        scanner = MarketScanner(exchange)
                        trade_manager = TradeManager(exchange, portfolio)
                        is_replay_mode = False
                        replay_provider = None
                        logger.info("🛑 Replay durduruldu, canlı moda dönüldü")
                        await redis_client.delete("replay:command")
                        continue
                    
                    # Komutu işlendi olarak işaretle
                    await redis_client.delete("replay:command")
            
            # Replay modu kontrolü
            if is_replay_mode and replay_provider:
                # Replay zamanını ilerlet
                replay_continue = await replay_provider.tick(real_time_seconds=1.0)
                if not replay_continue:
                    logger.info("🎬 REPLAY TAMAMLANDI!")
                    # Replay durumunu güncelle
                    await redis_client.set("replay:state", {
                        "status": "completed",
                        "final_balance": portfolio.get_balance()['total'],
                        "message": "Replay başarıyla tamamlandı"
                    })
                    # Canlı moda dön
                    exchange = ExchangeClient()
                    portfolio = PortfolioManager(exchange)
                    scanner = MarketScanner(exchange)
                    trade_manager = TradeManager(exchange, portfolio)
                    is_replay_mode = False
                    replay_provider = None
                    continue
                    
                logger.info(f"\n🎬 Replay Döngü #{cycle_count} @ {replay_provider.current_time}")
            else:
                logger.info(f"\n🔄 Döngü #{cycle_count} başlıyor...")

            # 0. Portföy Senkronizasyonu
            await portfolio.sync_positions()

            # 1. Açık pozisyonları kontrol et (TP/SL)
            await trade_manager.check_positions(scanner=scanner)

            # 2. Piyasayı tara
            signals = await scanner.scan_all()

            # 3. Sinyalleri işle
            # CRITICAL FIX: Prevent race condition - track processed symbols
            processed_symbols = set()
            for signal in signals:
                if not _running:
                    break
                
                # Skip if already processed in this cycle
                if signal['symbol'] in processed_symbols:
                    logger.debug(f"⏭️ {signal['symbol']} bu döngüde zaten işlendi, atlanıyor")
                    continue
                processed_symbols.add(signal['symbol'])

                can_open, reason = portfolio.can_open_position(signal['symbol'])
                if can_open:
                    notifier.notify_signal(signal)
                    success = await trade_manager.execute_signal(signal)
                    if success:
                        await asyncio.sleep(1)

            # 4. Günlük özet (sadece canlı modda)
            if not is_replay_mode:
                current_hour = datetime.now(timezone.utc).hour
                if current_hour == 0 and last_daily_report != 0:
                    stats = portfolio.get_stats()
                    stats['scanned'] = len(scanner.symbols)
                    notifier.notify_daily_summary(stats)
                    last_daily_report = 0
                elif current_hour != 0:
                    last_daily_report = current_hour

            # 5. Durum logu ve Redis güncelleme
            stats = portfolio.get_stats()
            stats['balance'] = portfolio.get_balance()['total']
            await redis_client.set("bot:stats", stats)
            
            # Replay durumunu güncelle
            if is_replay_mode and replay_provider:
                await redis_client.set("replay:state", {
                    "status": "running",
                    "current_time": replay_provider.current_time.isoformat(),
                    "progress_pct": replay_provider.get_progress(),
                    "balance": stats['balance'],
                    "open_positions": stats['open_positions']
                })
            
            logger.info(
                f"📊 Bakiye: ${stats['balance']:.2f} | "
                f"Açık: {stats['open_positions']} | "
                f"Günlük PnL: ${stats['daily_pnl']:+.2f} | "
                f"W/L: {stats['wins']}/{stats['losses']}"
            )

            # Bekleme
            if is_replay_mode:
                # Replay modunda her döngü 1 saniye (hızlandırılmış)
                await asyncio.sleep(0.1)
            else:
                for _ in range(SCAN_INTERVAL_SECONDS):
                    if not _running:
                        break
                    await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Döngü hatası: {e}", exc_info=True)
            if not is_replay_mode:
                notifier.notify_error(str(e))
            await asyncio.sleep(30)

    # Kapatma
    logger.info("🛑 Bot kapatılıyor...")
    if replay_provider:
        replay_provider.stop()
    await redis_client.close()
    if not is_replay_mode:
        notifier.send("🛑 <b>Bot Kapatıldı</b>")
    logger.info("👋 Güle güle!")


async def _init_replay_from_env():
    """ENV değişkenlerinden replay başlat"""
    try:
        provider = ReplayDataProvider(
            data_folder=REPLAY_DATA_FOLDER,
            speed_multiplier=REPLAY_SPEED
        )
        
        start_dt = datetime.strptime(REPLAY_START_DATE, "%Y-%m-%d")
        end_dt = datetime.strptime(REPLAY_END_DATE, "%Y-%m-%d")
        
        # Coin listesini al
        import os
        available_coins = []
        if os.path.exists(REPLAY_DATA_FOLDER):
            for f in os.listdir(REPLAY_DATA_FOLDER):
                if f.endswith('_USDT_USDT.csv') and not f.startswith('_'):
                    coin = f.replace('_USDT_USDT.csv', '')
                    available_coins.append(f"{coin}USDT")
        
        symbols = available_coins[:TOP_COINS_COUNT] if available_coins else ['BTCUSDT', 'ETHUSDT']
        
        provider.initialize_replay(
            symbols=symbols,
            start_date=start_dt,
            end_date=end_dt,
            speed=REPLAY_SPEED
        )
        
        logger.info(f"📼 Replay (ENV) başlatıldı: {len(symbols)} coin")
        return provider
        
    except Exception as e:
        logger.error(f"❌ Replay başlatma hatası: {e}")
        return None


async def _init_replay_from_api(config: dict):
    """API'den gelen konfigürasyonla replay başlat"""
    try:
        from datetime import datetime
        
        provider = ReplayDataProvider(
            data_folder=REPLAY_DATA_FOLDER,
            speed_multiplier=config.get('speed', 100)
        )
        
        start_dt = datetime.strptime(config['start_date'], "%Y-%m-%d")
        end_dt = datetime.strptime(config['end_date'], "%Y-%m-%d")
        
        # API'den gelen symbol listesi veya tümü
        symbols = config.get('symbols', [])
        if not symbols:
            # Tüm mevcut coinleri kullan
            import os
            symbols = []
            if os.path.exists(REPLAY_DATA_FOLDER):
                for f in os.listdir(REPLAY_DATA_FOLDER):
                    if f.endswith('_USDT_USDT.csv') and not f.startswith('_'):
                        coin = f.replace('_USDT_USDT.csv', '')
                        symbols.append(f"{coin}USDT")
        
        provider.initialize_replay(
            symbols=symbols[:TOP_COINS_COUNT],
            start_date=start_dt,
            end_date=end_dt,
            speed=config.get('speed', 100)
        )
        
        logger.info(f"📼 Replay (API) başlatıldı: {len(symbols)} coin @ {config.get('speed', 100)}x")
        return provider
        
    except Exception as e:
        logger.error(f"❌ API Replay başlatma hatası: {e}")
        return None

async def _async_shutdown():
    global _running
    logger.info("🛑 Kapatma sinyali alındı...")
    _running = False

if __name__ == "__main__":
    asyncio.run(main())
