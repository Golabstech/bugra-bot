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


# 🎯 TP / SL
# 🎯 TP / SL
TP1_CLOSE_PCT = 0.35
TP2_CLOSE_PCT = 0.35
TP3_CLOSE_PCT = 0.30
SL_ATR_MULT = float(os.getenv("SL_ATR_MULT", "2.4"))
TP1_RR = float(os.getenv("TP1_RR", "1.5"))
TP2_RR = float(os.getenv("TP2_RR", "3.0"))
TP3_RR = float(os.getenv("TP3_RR", "5.0"))

# TP1 sonrası SL nereye çekilsin? (0.5 = riskin %50'sine, 0.0 = breakeven)
TP1_SL_RETRACE = 0.5
TAKER_FEE = 0.0005 # %0.05

# ==========================================
# 🛡️ RİSK YÖNETİMİ
# ==========================================
POSITION_SIZE_PCT = float(os.getenv("POSITION_SIZE_PCT", "5.0"))
LEVERAGE = int(os.getenv("LEVERAGE", "10"))
MAX_RISK_PCT = float(os.getenv("MAX_RISK_PCT", "10.0"))
MAX_CONCURRENT_POSITIONS = int(os.getenv("MAX_CONCURRENT_POSITIONS", "5"))
DAILY_LOSS_LIMIT_PCT = float(os.getenv("DAILY_LOSS_LIMIT_PCT", "2.0"))

# Cooldown & Blacklist
COIN_BLACKLIST_AFTER = 2     # 2 ardışık zarar sonrası blacklist
COIN_BLACKLIST_CANDLES = 120 # Blacklist süresi (1m mumda 2 saat)
COOLDOWN_CANDLES = 20        # Her işlem sonrası soğuma
HARD_STOP_LOSS_PCT = 5.0    # Acil durum %5 stop

# Flip Stratejisi (Opsiyonel)
STRATEGY_SIDE = 'BOTH' # 'LONG' | 'SHORT' | 'BOTH'
ENABLE_FLIP_STRATEGY = os.getenv("ENABLE_FLIP_STRATEGY", "false").lower() == "true"
FLIP_TP1_PCT = 1.0
FLIP_TP2_PCT = 2.0
FLIP_SL_PCT = 0.8

# ==========================================
# 📊 STRATEJİ (MOMENTUM SCALPING)
# ==========================================
MOMENTUM_THRESHOLD_PCT = float(os.getenv("MOMENTUM_THRESHOLD_PCT", "1.5")) # %1.5 yükseliş
VOLUME_THRESHOLD_MUL = float(os.getenv("VOLUME_THRESHOLD_MUL", "1.5"))    # Ortalama hacmin 1.5 katı
COOLDOWN_SECONDS = int(os.getenv("COOLDOWN_SECONDS", "300"))              # 5 dakika
MIN_24H_VOLUME = float(os.getenv("MIN_24H_VOLUME", "50000000"))           # 50M $

# 🔄 MULTI-TIMEFRAME CONFIRMATION
MTF_ENABLED = os.getenv("MTF_ENABLED", "true").lower() == "true"
MTF_TIMEFRAME = os.getenv("MTF_TIMEFRAME", "15m")  # Üst zaman dilimi (15m veya 1h)
MTF_EMA_FAST = int(os.getenv("MTF_EMA_FAST", "9"))   # Hızlı EMA
MTF_EMA_SLOW = int(os.getenv("MTF_EMA_SLOW", "21"))  # Yavaş EMA

# 🎯 PULLBACK ENTRY (Geri çekilmede giriş)
PULLBACK_ENABLED = os.getenv("PULLBACK_ENABLED", "true").lower() == "true"
PULLBACK_TIMEOUT_CANDLES = int(os.getenv("PULLBACK_TIMEOUT_CANDLES", "10"))  # 10 mum içinde gelmezse iptal

# 📈 KADEMELİ FİBONACCI GİRİŞİ
# Her seviyede belirli bir yüzde pozisyon açılır
FIB_LEVELS = [0.382, 0.50, 0.618]  # Fibonacci geri çekilme seviyeleri
FIB_TIER_ALLOCATIONS = {
    0.382: 0.25,  # %25 pozisyon (hızlı pullback)
    0.50: 0.25,   # %25 pozisyon (orta pullback) 
    0.618: 0.50,  # %50 pozisyon (derin pullback)
}

# ==========================================
# 📼 REPLAY MODE (Backtest Verisi ile Canlı Simülasyon)
# ==========================================
REPLAY_MODE = os.getenv("REPLAY_MODE", "false").lower() == "true"
REPLAY_DATA_FOLDER = os.getenv("REPLAY_DATA_FOLDER", "backtest_data")
REPLAY_SPEED = float(os.getenv("REPLAY_SPEED", "100"))  # 100x hızlı
REPLAY_START_DATE = os.getenv("REPLAY_START_DATE", "2026-01-15")  # YYYY-MM-DD
REPLAY_END_DATE = os.getenv("REPLAY_END_DATE", "2026-01-20")  # YYYY-MM-DD

# ==========================================
# ⏱️ TARAMA AYARLARI
# ==========================================
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "10")) # 10 saniye (Hızlı Tarama)
TIMEFRAME = os.getenv("TIMEFRAME", "1m")
OHLCV_LIMIT = int(os.getenv("OHLCV_LIMIT", "50"))
TOP_COINS_COUNT = int(os.getenv("TOP_COINS_COUNT", "200"))

# ==========================================
# 📊 REDIS & ALTYAPI
# ==========================================
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
BOT_ROLE = os.getenv("BOT_ROLE", "worker") # worker | api

# ==========================================
# 📋 LOGLAMA
# ==========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
