"""
⚙️ Merkezi konfigürasyon - .env + varsayılan değerler
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# .env dosyasını proje kökünden yükle
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# ==========================================
# 🔑 BORSA API
# ==========================================
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
EXCHANGE_SANDBOX = os.getenv("EXCHANGE_SANDBOX", "true").lower() == "true"

# ==========================================
# 📲 TELEGRAM
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ==========================================
# 💰 POZİSYON & KALDIRAÇ
# ==========================================
LEVERAGE = int(os.getenv("LEVERAGE", "5"))
POSITION_SIZE_PCT = float(os.getenv("POSITION_SIZE_PCT", "10"))
MAKER_FEE = 0.0002
TAKER_FEE = 0.0005

# ==========================================
# 🛡️ RİSK YÖNETİMİ
# ==========================================
MAX_RISK_PCT = float(os.getenv("MAX_RISK_PCT", "50"))
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "5"))
DAILY_LOSS_LIMIT_PCT = float(os.getenv("DAILY_LOSS_LIMIT_PCT", "10"))

# ==========================================
# ⚡ STRATEJİ FİLTRELERİ
# ==========================================
STRATEGY_SIDE = os.getenv("STRATEGY_SIDE", "SHORT")
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "80")) # 85 -> 80 (Test Modu)

MIN_REASONS = int(os.getenv("MIN_REASONS", "4"))
COOLDOWN_CANDLES = int(os.getenv("COOLDOWN_CANDLES", "5")) # 8 -> 5 (Daha hızlı tekrar giriş)
COIN_BLACKLIST_AFTER = int(os.getenv("COIN_BLACKLIST_AFTER", "3"))
COIN_BLACKLIST_CANDLES = int(os.getenv("COIN_BLACKLIST_CANDLES", "32"))

# 🎯 VOLATİLİTE
MAX_ATR_PERCENT = float(os.getenv("MAX_ATR_PERCENT", "4.5"))
MIN_ATR_PERCENT = float(os.getenv("MIN_ATR_PERCENT", "0.5"))
HARD_STOP_LOSS_PCT = float(os.getenv("HARD_STOP_LOSS_PCT", "3.5")) # %7 -> %3.5 (Acımasız Stop)

# 🎯 TP / SL
# 🎯 TP / SL
TP1_CLOSE_PCT = 0.40
TP2_CLOSE_PCT = 0.30
TP3_CLOSE_PCT = 0.30
SL_ATR_MULT = float(os.getenv("SL_ATR_MULT", "2.0"))  # 2.4 -> 2.0 (Daha Sıkı)
TP1_RR = float(os.getenv("TP1_RR", "1.3"))          # 1.8 -> 1.3 (Vur-Kaç)
TP2_RR = float(os.getenv("TP2_RR", "2.4"))          # 2.8 -> 2.4
TP3_RR = float(os.getenv("TP3_RR", "4.0"))          # 4.5 -> 4.0

# 🧪 DARWINIST (SIGNAL DECAY) AYARLARI
SIGNAL_DECAY_THRESHOLD = 20    # Skor bu değerin altına düşerse tahliye et (25 -> 20: Daha Sabırlı)
SIGNAL_DECAY_GRACE_PERIOD = 4  # İlk 4 mumda tahliye yapma (gürültü koruması)

# 🔄 FLIP STRATEGY (Squeeze sonrası ters işlem)
ENABLE_FLIP_STRATEGY = os.getenv("ENABLE_FLIP", "true").lower() == "true"
FLIP_TP1_PCT = 1.2  # %1.2 kârda ilk çıkış
FLIP_TP2_PCT = 3.0  # %3.0 kârda tam çıkış
FLIP_SL_PCT = 2.0   # %2.0 stop

# ==========================================
# ⏱️ TARAMA AYARLARI
# ==========================================
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "30")) # 60 -> 30 (Hızlı Test)
TIMEFRAME = os.getenv("TIMEFRAME", "15m")
OHLCV_LIMIT = int(os.getenv("OHLCV_LIMIT", "100"))
TOP_COINS_COUNT = int(os.getenv("TOP_COINS_COUNT", "100"))

# ==========================================
# 📊 REDIS & ALTYAPI
# ==========================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BOT_ROLE = os.getenv("BOT_ROLE", "worker") # worker | api

# ==========================================
# 📋 LOGLAMA
# ==========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
