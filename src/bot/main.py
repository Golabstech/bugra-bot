"""
🚀 Ana Bot Döngüsü
Tüm modülleri orkestra eder: Tarama → Sinyal → İşlem → Takip
"""
import time
import logging
import signal as sig
import sys
from datetime import datetime, timezone

from .config import SCAN_INTERVAL_SECONDS, LOG_LEVEL
from .exchange import ExchangeClient
from .scanner import MarketScanner
from .portfolio import PortfolioManager
from .trader import TradeManager
from . import notifier

# Loglama
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(name)-10s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("bot")

# Graceful shutdown
_running = True

def _shutdown(signum, frame):
    global _running
    logger.info("🛑 Kapatma sinyali alındı...")
    _running = False

sig.signal(sig.SIGINT, _shutdown)
sig.signal(sig.SIGTERM, _shutdown)


def main():
    """Ana giriş noktası"""
    logger.info("=" * 60)
    logger.info("🤖 BUGRA-BOT v1.3.0 — Canlı Trading Motoru")
    logger.info("=" * 60)

    # Modülleri başlat
    exchange = ExchangeClient()
    portfolio = PortfolioManager(exchange)
    scanner = MarketScanner(exchange)
    trade_manager = TradeManager(exchange, portfolio)

    # Bağlantı testi
    balance = portfolio.get_balance()
    if balance['total'] <= 0:
        logger.error("❌ Bakiye alınamadı veya sıfır. API key'leri kontrol edin.")
        notifier.notify_error("Bakiye alınamadı! API key kontrol edin.")
        return

    logger.info(f"💰 Bakiye: ${balance['total']:.2f} (Free: ${balance['free']:.2f})")
    notifier.send(
        f"🤖 <b>Bot Başlatıldı</b>\n"
        f"💰 Bakiye: ${balance['total']:.2f}\n"
        f"⏱️ Tarama: her {SCAN_INTERVAL_SECONDS}s"
    )

    last_daily_report = datetime.now(timezone.utc).hour
    cycle_count = 0

    # Ana döngü
    while _running:
        try:
            cycle_count += 1
            logger.info(f"\n🔄 Döngü #{cycle_count} başlıyor...")

            # 1. Açık pozisyonları kontrol et (TP/SL)
            trade_manager.check_positions()

            # 2. Piyasayı tara
            signals = scanner.scan_all()

            # 3. Sinyalleri işle (en yüksek skordan başla)
            for signal in signals:
                if not _running:
                    break

                can_open, reason = portfolio.can_open_position(signal['symbol'])
                if can_open:
                    notifier.notify_signal(signal)
                    success = trade_manager.execute_signal(signal)
                    if success:
                        time.sleep(1)  # Emir arası bekleme

            # 4. Günlük özet (her gün saat 00:00 UTC'de)
            current_hour = datetime.now(timezone.utc).hour
            if current_hour == 0 and last_daily_report != 0:
                stats = portfolio.get_stats()
                stats['scanned'] = len(scanner.symbols)
                notifier.notify_daily_summary(stats)
                last_daily_report = 0
            elif current_hour != 0:
                last_daily_report = current_hour

            # 5. Durum logu
            stats = portfolio.get_stats()
            logger.info(
                f"📊 Bakiye: ${stats['balance']:.2f} | "
                f"Açık: {stats['open_positions']} | "
                f"Günlük PnL: ${stats['daily_pnl']:+.2f} | "
                f"W/L: {stats['wins']}/{stats['losses']}"
            )

            # Sonraki döngüyü bekle
            logger.info(f"⏳ {SCAN_INTERVAL_SECONDS}s bekleniyor...")
            for _ in range(SCAN_INTERVAL_SECONDS):
                if not _running:
                    break
                time.sleep(1)

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"❌ Döngü hatası: {e}", exc_info=True)
            notifier.notify_error(str(e))
            time.sleep(30)

    # Kapatma
    logger.info("🛑 Bot kapatılıyor...")
    notifier.send("🛑 <b>Bot Kapatıldı</b>")
    logger.info("👋 Güle güle!")


if __name__ == "__main__":
    main()
