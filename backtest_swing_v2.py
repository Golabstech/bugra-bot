import pandas as pd
import pandas_ta as ta
import warnings
import os
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

warnings.filterwarnings('ignore')

# ==========================================
# ⚙️ SWING BACKTEST v2 - GÜÇLENDIRILMIŞ
# ==========================================
# Yenilikler:
#   1. BTC verisinden GERÇEK trend analizi (her mum için)
#   2. Simüle L/S oranı (BTC fiyat aksiyonundan)
#   3. Destek/Direnç seviyeleri (Pivot, Swing H/L)
#   4. Market rejimi: BULL / BEAR / NEUTRAL → yön kilidi
#   5. Yanlış sinyal → o coin + yön için günlük ban
#   6. Max kayıp limiti (tek işlem başına)
#   7. BB genişliği, MA eğimi, çoklu onay zorunluluğu
# ==========================================

DATA_FOLDER = "backtest_data"
INITIAL_BALANCE = 200
POSITION_SIZE_PCT = 25    # Bakiyeyi 4'e böl, her işlem %25
MAX_CONCURRENT = 4        # Aynı anda max 4 pozisyon

# Tarih Araligi (15 Ocak - 10 Subat ~27 gun)
BACKTEST_START = datetime(2026, 1, 15, 0, 0, 0)
BACKTEST_END = datetime(2026, 2, 10, 23, 59, 59)

SINGLE_COIN = None
SHOW_TRADE_DETAILS = True

# STRATEJI FILTRELERI
SCORE_THRESHOLD = 60           # Her iki yon icin ayni esik
MIN_WIN_RATE = 60
COOLDOWN_CANDLES = 12          # Genel cooldown (12 mum = 3 saat)
COOLDOWN_AFTER_LOSS = 20       # Kayiptan sonra cooldown (20 mum = 5 saat)
MAX_TRADES_PER_COIN = 8        # Max islem / coin
MIN_CONFIRMATION_COUNT = 3     # En az 3 farkli indikator onay
MAX_CONSECUTIVE_LOSSES_COIN = 2  # Ayni coinde ust uste 2 kayiptan sonra o coin bitti

# ISLEM SURESI LIMITLERI (15dk mumlar icin)
MIN_HOLD_CANDLES = 2           # Min 30 dakika (2 mum)
MAX_HOLD_CANDLES = 16          # Max 4 saat (16 mum)
PREFERRED_MIN_CANDLES = 4      # Ideal min 1 saat (4 mum)

# HACIM FILTRESI
MIN_24H_VOLUME_USD = 20_000_000  # Min 20M USD 24 saatlik hacim

# VOLATILITE FILTRESI
MAX_ATR_PERCENT = 5.0
MIN_ATR_PERCENT = 0.3

# ==========================================
# 🏷️ COIN TIER SINIFLANDIRMASI (Market Cap)
# ==========================================
# TOP: İlk ~50 - en stabil, en likit
# MID: 50-100 arası - orta likidite
# SMALL: 100+ veya yeni/meme - yüksek volatilite riski

TOP_TIER_COINS = {
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'AVAX', 'DOT', 'LINK',
    'NEAR', 'ATOM', 'LTC', 'BCH', 'ICP', 'HBAR', 'APT', 'ARB', 'OP', 'MKR',
    'FIL', 'SEI', 'SUI', 'ONDO', 'JUP', 'HYPE', 'ENA', 'AAVE', 'CRV', 'GALA',
    'AXS', 'DYDX', 'MNT', 'PAXG', 'PENGU', 'TON', 'TRX', 'UNI', 'XLM', 'XMR',
    'TAO', 'WLD', 'TRUMP', 'STG', 'STRK', 'ZEC', 'FLOW', 'DASH',
    '1000PEPE', '1000SHIB', '1000BONK', 'WIF', 'VIRTUAL'
}

MID_TIER_COINS = {
    'BERA', 'KAITO', 'MOCA', 'IP', 'OCEAN', 'ZRO', 'ROSE', 'DGB', 'ZIL',
    'AXL', 'OMNI', 'SNT', 'AUCTION', 'BSW', 'LIT', 'HIFI', 'REN', 'DUSK',
    'FARTCOIN', 'CHESS', 'ZK', 'KITE', 'AMB', 'MINA', 'POL', 'MYX',
    'SHIB1000', 'XRP', '1000SHIB'
}
# SMALL_TIER: Yukarıdaki listelerde olmayan tüm coinler

def get_coin_tier(symbol):
    """Coin'in market cap tier'ını belirle."""
    coin = symbol.split('/')[0].split(':')[0].upper()
    if coin in TOP_TIER_COINS:
        return 'TOP'
    elif coin in MID_TIER_COINS:
        return 'MID'
    return 'SMALL'


def get_coin_volatility_class(df, idx, lookback=20):
    """
    Son N mumun ATR yüzdesine göre coin volatilite sınıfı hesapla.
    Returns: ('LOW', 'MEDIUM', 'HIGH', 'EXTREME') ve ATR%
    """
    if idx < lookback or idx >= len(df):
        return 'MEDIUM', 2.0
    
    atr_pcts = []
    for j in range(max(0, idx - lookback), idx + 1):
        row_j = df.iloc[j]
        atr_val = float(row_j['atr']) if pd.notna(row_j.get('atr', None)) else 0
        price_val = float(row_j['close']) if float(row_j['close']) > 0 else 1
        if atr_val > 0 and price_val > 0:
            atr_pcts.append((atr_val / price_val) * 100)
    
    if not atr_pcts:
        return 'MEDIUM', 2.0
    
    avg_atr_pct = np.mean(atr_pcts)
    
    if avg_atr_pct > 4.0:
        return 'EXTREME', avg_atr_pct
    elif avg_atr_pct > 2.5:
        return 'HIGH', avg_atr_pct
    elif avg_atr_pct > 1.0:
        return 'MEDIUM', avg_atr_pct
    else:
        return 'LOW', avg_atr_pct


def get_dynamic_sl_mult(vol_class, coin_tier):
    """Volatiliteye göre SL ATR çarpanı. Volatil coin → daha sıkı SL."""
    if vol_class == 'EXTREME':
        return 1.0   # Çok sıkı SL
    elif vol_class == 'HIGH':
        return 1.1 if coin_tier == 'SMALL' else 1.2
    elif vol_class == 'MEDIUM':
        return 1.3 if coin_tier == 'SMALL' else 1.5
    else:  # LOW
        return 1.5


def get_dynamic_max_loss(vol_class, coin_tier):
    """Volatiliteye göre max kayıp yüzdesi. Volatil → daha sıkı limit."""
    if vol_class == 'EXTREME':
        return -10.0
    elif vol_class == 'HIGH':
        if coin_tier == 'SMALL':
            return -10.0
        return -15.0
    elif vol_class == 'MEDIUM':
        if coin_tier == 'SMALL':
            return -15.0
        return -18.0
    else:  # LOW
        return -20.0


def get_volatility_score_penalty(vol_class, coin_tier, regime_strength):
    """
    Volatil piyasada küçük coinler için ek skor gereksinimi.
    Returns: Ek skor eşiği (bu kadar fazla skor gerekir)
    """
    penalty = 0
    # Piyasa stresi yüksekse (rejim gücü >= 50)
    market_stressed = regime_strength >= 50
    
    if market_stressed:
        if coin_tier == 'SMALL':
            penalty += 15  # SMALL coin + stresli piyasa → +15 skor gerek
        elif coin_tier == 'MID':
            penalty += 10  # MID coin + stresli piyasa → +10 skor gerek
    
    if vol_class == 'EXTREME':
        penalty += 15  # Extreme volatilite → +15 ek skor
    elif vol_class == 'HIGH':
        penalty += 10  # Yüksek volatilite → +10 ek skor
    
    return penalty


# 🎯 PARTIAL TP ORANLARI
TP1_CLOSE_PCT = 0.40
TP2_CLOSE_PCT = 0.35
TP3_CLOSE_PCT = 0.25

# 🎯 SL VE TP ÇARPANLARI
SL_ATR_MULT = 1.5
TP1_RR = 1.2
TP2_RR = 2.0
TP3_RR = 3.0

TRAILING_STOP = True
PARTIAL_TP = True

# 🛡️ MAX KAYIP LİMİTİ (tek işlem başına)
MAX_LOSS_PER_TRADE_PCT = -25.0   # Tek işlemde max -%25

# KALDIRAC (dinamik: 5x-10x, BTC durumuna gore)
def get_leverage(score, win_rate, market_regime, btc_strength=0, confirmations=3, direction='LONG', vol_class='MEDIUM', coin_tier='TOP'):
    """Market rejimi, BTC gucu, yon uyumu, volatilite ve coin tier'a gore kaldirac. Min 5, Max 10."""
    base = 5
    
    # Skor + win rate bazli
    if score >= 90 and win_rate >= 80:
        base = 10
    elif score >= 85 and win_rate >= 75:
        base = 9
    elif score >= 80 and win_rate >= 70:
        base = 8
    elif score >= 70 and win_rate >= 65:
        base = 7
    elif score >= 60:
        base = 6
    
    # Onay sayisi bonusu
    if confirmations >= 6:
        base = min(base + 1, 10)
    elif confirmations <= 3:
        base = max(base - 1, 5)
    
    # BTC guc bonusu
    if btc_strength >= 60:
        base = min(base + 1, 10)
    elif btc_strength <= 20:
        base = max(base - 1, 5)
    
    # YON UYUMU: Trend ile ayni yone +2, ters yone -2
    trend_aligned = (direction == 'LONG' and market_regime == 'BULL') or \
                    (direction == 'SHORT' and market_regime == 'BEAR')
    counter_trend = (direction == 'LONG' and market_regime == 'BEAR') or \
                    (direction == 'SHORT' and market_regime == 'BULL')
    if trend_aligned:
        base = min(base + 2, 10)
    elif counter_trend:
        base = max(base - 2, 5)
    elif market_regime == 'NEUTRAL':
        base = max(base - 1, 5)
    
    # ═══ VOLATILITE SINIRLAMASI ═══
    # Yüksek volatilite → kaldıracı sınırla (en son uygulanır)
    if vol_class == 'EXTREME':
        base = 5  # Her zaman 5x - extreme vol çok tehlikeli
    elif vol_class == 'HIGH':
        if coin_tier == 'SMALL':
            base = min(base, 5)  # Small + High vol = kesinlikle 5x
        elif coin_tier == 'MID':
            base = min(base, 6)  # Mid + High vol = max 6x
        else:
            base = min(base, 7)  # Top + High vol = max 7x
    elif vol_class == 'MEDIUM':
        if coin_tier == 'SMALL':
            base = min(base, 7)  # Small + Medium vol = max 7x
    # LOW vol + TOP tier → normal kaldıraç (sınırlama yok)
    
    return max(5, min(10, base))

# ==========================================
# ₿ BTC TREND ANALİZİ (MUM BAZLI)
# ==========================================

def load_btc_data():
    """BTC verisini yükle ve trend indikatörlerini hesapla."""
    btc_file = os.path.join(DATA_FOLDER, "BTC_USDT_USDT.csv")
    if not os.path.exists(btc_file):
        print("⚠️ BTC verisi bulunamadı! Trend analizi devre dışı.")
        return None
    
    df = pd.read_csv(btc_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Trend indikatörleri
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['ema200'] = ta.ema(df['close'], length=200)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    if macd is not None:
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 1]
        df['macd_hist'] = macd.iloc[:, 2]
    else:
        df['macd'] = df['macd_signal'] = df['macd_hist'] = 0
    
    adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
    if adx_data is not None:
        df['adx'] = adx_data.iloc[:, 0]
        df['di_plus'] = adx_data.iloc[:, 1]
        df['di_minus'] = adx_data.iloc[:, 2]
    else:
        df['adx'] = df['di_plus'] = df['di_minus'] = 0
    
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    
    # Volume MA
    df['vol_sma20'] = ta.sma(df['volume'], length=20)
    
    df = df.ffill().fillna(0)
    return df


def precompute_btc_regimes(btc_df):
    """
    BTC rejimini her satır için önceden hesapla.
    Returns: dict {timestamp -> (regime, strength, ls_ratio)}
    """
    if btc_df is None:
        return {}
    
    regimes = {}
    up_candle_rolling = (btc_df['close'] > btc_df['open']).rolling(20).sum()
    
    for i in range(50, len(btc_df)):
        row = btc_df.iloc[i]
        ts = row['timestamp']
        price = float(row['close'])
        ema9 = float(row['ema9'])
        ema21 = float(row['ema21'])
        ema50 = float(row['ema50'])
        ema200 = float(row['ema200']) if row['ema200'] != 0 else ema50
        rsi = float(row['rsi'])
        macd_val = float(row['macd'])
        macd_sig = float(row['macd_signal'])
        macd_hist = float(row['macd_hist'])
        adx = float(row['adx'])
        di_plus = float(row['di_plus'])
        di_minus = float(row['di_minus'])
        
        bull_score = 0
        bear_score = 0
        
        # 1. EMA dizilimi (40p)
        if price > ema200 and ema50 > ema200:
            bull_score += 20
        elif price < ema200 and ema50 < ema200:
            bear_score += 20
        
        if price > ema9 > ema21 > ema50:
            bull_score += 20
        elif price < ema9 < ema21 < ema50:
            bear_score += 20
        elif price > ema21:
            bull_score += 10
        elif price < ema21:
            bear_score += 10
        
        # 2. RSI (15p)
        if rsi > 60: bull_score += 15
        elif rsi < 40: bear_score += 15
        elif rsi > 50: bull_score += 5
        elif rsi < 50: bear_score += 5
        
        # 3. MACD (15p)
        if macd_val > macd_sig and macd_hist > 0: bull_score += 15
        elif macd_val < macd_sig and macd_hist < 0: bear_score += 15
        
        # 4. ADX + DI (20p)
        if adx > 25:
            if di_plus > di_minus: bull_score += 20
            else: bear_score += 20
        elif adx > 15:
            if di_plus > di_minus: bull_score += 10
            else: bear_score += 10
        
        # 5. Son 20 mumun yönü (10p)
        up_count = up_candle_rolling.iloc[i] if pd.notna(up_candle_rolling.iloc[i]) else 10
        if up_count >= 13: bull_score += 10
        elif (20 - up_count) >= 13: bear_score += 10
        
        # L/S Ratio simülasyonu
        ls_ratio = 1.0
        if rsi > 60 and macd_hist > 0:
            ls_ratio = 1.2 + (rsi - 60) / 100
        elif rsi < 40 and macd_hist < 0:
            ls_ratio = 0.8 - (40 - rsi) / 100
        
        vol = float(row['volume']) if pd.notna(row['volume']) else 0
        vol_sma = float(row['vol_sma20']) if pd.notna(row['vol_sma20']) else vol
        if vol_sma > 0 and vol > vol_sma * 2:
            if row['close'] < row['open']:
                bear_score += 10
                ls_ratio *= 0.85
            else:
                bull_score += 10
                ls_ratio *= 1.15
        
        # Sonuç
        total = bull_score + bear_score
        if total == 0:
            regimes[ts] = ('NEUTRAL', 0, 1.0)
        elif bull_score >= bear_score + 20:
            regimes[ts] = ('BULL', bull_score, ls_ratio)
        elif bear_score >= bull_score + 20:
            regimes[ts] = ('BEAR', bear_score, ls_ratio)
        else:
            regimes[ts] = ('NEUTRAL', max(bull_score, bear_score), ls_ratio)
    
    return regimes


def get_btc_regime_fast(btc_regimes, current_time, btc_timestamps):
    """
    Pre-computed rejimlerden en yakın BTC rejimini al.
    Binary search ile hızlı lookup.
    """
    if not btc_regimes or len(btc_timestamps) == 0:
        return 'NEUTRAL', 0, 1.0
    
    # En yakın (geçmişteki) timestamp'i bul
    idx = np.searchsorted(btc_timestamps, current_time, side='right') - 1
    if idx < 0:
        return 'NEUTRAL', 0, 1.0
    
    ts = btc_timestamps[idx]
    return btc_regimes.get(ts, ('NEUTRAL', 0, 1.0))


# ==========================================
# 📊 DESTEK / DİRENÇ SEVİYELERİ
# ==========================================

def calculate_support_resistance(df, lookback=96):
    """
    Son N mumdan destek ve direnç seviyeleri hesapla.
    Pivot Points + Swing High/Low.
    96 mum = 24 saat (15m TF)
    """
    if len(df) < 10:
        close = float(df.iloc[-1]['close'])
        return {
            'pivot': close, 'r1': close*1.01, 'r2': close*1.02,
            's1': close*0.99, 's2': close*0.98,
            'nearest_support': close*0.99, 'nearest_resistance': close*1.01,
            'swing_highs': [], 'swing_lows': [],
            'range_high': close*1.01, 'range_low': close*0.99
        }
    
    if len(df) < lookback:
        lookback = len(df)
    
    recent = df.tail(lookback).reset_index(drop=True)
    
    # Pivot Point (Klasik)
    high = recent['high'].max()
    low = recent['low'].min()
    close = float(df.iloc[-1]['close'])
    pivot = (high + low + close) / 3
    
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    
    # Swing High/Low - numpy ile hızlı hesapla
    highs = recent['high'].values
    lows = recent['low'].values
    swing_highs = []
    swing_lows = []
    
    for i in range(5, len(highs) - 5):
        window_h = highs[i-5:i+6]
        window_l = lows[i-5:i+6]
        if highs[i] == window_h.max():
            swing_highs.append(float(highs[i]))
        if lows[i] == window_l.min():
            swing_lows.append(float(lows[i]))
    
    # En yakın destek ve direnç
    supports = sorted(set([s1, s2] + swing_lows), reverse=True)
    resistances = sorted(set([r1, r2] + swing_highs))
    
    nearest_support = None
    nearest_resistance = None
    
    for s in supports:
        if s < close:
            nearest_support = s
            break
    
    for r in resistances:
        if r > close:
            nearest_resistance = r
            break
    
    return {
        'pivot': pivot,
        'r1': r1, 'r2': r2,
        's1': s1, 's2': s2,
        'nearest_support': nearest_support or s1,
        'nearest_resistance': nearest_resistance or r1,
        'swing_highs': swing_highs[-3:] if swing_highs else [],
        'swing_lows': swing_lows[-3:] if swing_lows else [],
        'range_high': high,
        'range_low': low
    }


def check_sr_quality(price, direction, sr_data, atr):
    """
    Destek/direnç seviyelerine göre işlem kalitesini değerlendir.
    Returns: bonus puan ve nedenler
    """
    bonus = 0
    reasons = []
    
    support = sr_data['nearest_support']
    resistance = sr_data['nearest_resistance']
    pivot = sr_data['pivot']
    
    if direction == 'LONG':
        # LONG: Desteğe yakınlık iyi, dirençe uzaklık iyi
        dist_to_support = abs(price - support) / atr if atr > 0 else 999
        dist_to_resistance = abs(resistance - price) / atr if atr > 0 else 0
        
        # Destek yakınında mı? (2 ATR içinde)
        if dist_to_support < 2.0:
            bonus += 15
            reasons.append(f"S/R: Destek yakın ({dist_to_support:.1f}ATR)")
        
        # Pivotun üstünde mi?
        if price > pivot:
            bonus += 5
            reasons.append("S/R: Pivot üstü")
        
        # Dirençe yeterli mesafe var mı? (en az 2 ATR)
        if dist_to_resistance < 1.0:
            bonus -= 15
            reasons.append(f"S/R: Direnç çok yakın! ({dist_to_resistance:.1f}ATR)")
        elif dist_to_resistance >= 2.0:
            bonus += 5
            reasons.append(f"S/R: Direnç uzak ({dist_to_resistance:.1f}ATR)")
    
    elif direction == 'SHORT':
        # SHORT: Dirence yakınlık iyi, desteğe uzaklık iyi
        dist_to_resistance = abs(price - resistance) / atr if atr > 0 else 999
        dist_to_support = abs(price - support) / atr if atr > 0 else 0
        
        # Direnç yakınında mı?
        if dist_to_resistance < 2.0:
            bonus += 15
            reasons.append(f"S/R: Direnç yakın ({dist_to_resistance:.1f}ATR)")
        
        # Pivotun altında mı?
        if price < pivot:
            bonus += 5
            reasons.append("S/R: Pivot altı")
        
        # Desteğe yeterli mesafe var mı?
        if dist_to_support < 1.0:
            bonus -= 15
            reasons.append(f"S/R: Destek çok yakın! ({dist_to_support:.1f}ATR)")
        elif dist_to_support >= 2.0:
            bonus += 5
            reasons.append(f"S/R: Destek uzak ({dist_to_support:.1f}ATR)")
    
    return bonus, reasons


# ==========================================
# 📊 İNDİKATÖR HESAPLAMA
# ==========================================

def calculate_indicators(df):
    """Genişletilmiş indikatörler."""
    df = df.copy()
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['sma100'] = ta.sma(df['close'], length=100)
    df['sma200'] = ta.sma(df['close'], length=200)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    macd = ta.macd(df['close'])
    if macd is not None:
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 1]
        df['macd_hist'] = macd.iloc[:, 2]
    else:
        df['macd'] = df['macd_signal'] = df['macd_hist'] = 0
    
    bb = ta.bbands(df['close'], length=20, std=2)
    if bb is not None:
        df['bb_lower'] = bb.iloc[:, 0]
        df['bb_mid'] = bb.iloc[:, 1]
        df['bb_upper'] = bb.iloc[:, 2]
        df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']  # BB genişliği
    else:
        df['bb_pct'] = 0.5
        df['bb_width'] = 0
        df['bb_lower'] = df['bb_upper'] = df['bb_mid'] = df['close']
    
    adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
    if adx_data is not None:
        df['adx'] = adx_data.iloc[:, 0]
        df['di_plus'] = adx_data.iloc[:, 1]
        df['di_minus'] = adx_data.iloc[:, 2]
    else:
        df['adx'] = df['di_plus'] = df['di_minus'] = 0
    
    stoch = ta.stochrsi(df['close'], length=14)
    if stoch is not None:
        df['stoch_k'] = stoch.iloc[:, 0]
    else:
        df['stoch_k'] = 50
    
    df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['vol_sma'] = ta.sma(df['volume'], length=20)
    
    # 24 saatlik USD hacim (96 mum = 24 saat, 15dk timeframe)
    df['vol_usd'] = df['volume'] * df['close']
    df['vol_usd_24h'] = df['vol_usd'].rolling(window=96, min_periods=48).sum()
    
    # MA Egimleri (slope) - son 5 mumun trendini gosterir
    df['ema9_slope'] = df['ema9'].diff(5) / df['ema9'].shift(5) * 100
    df['ema21_slope'] = df['ema21'].diff(5) / df['ema21'].shift(5) * 100
    df['ema50_slope'] = df['ema50'].diff(10) / df['ema50'].shift(10) * 100
    
    df = df.ffill().fillna(0)
    return df


# ==========================================
# 🔍 ÇİFT YÖNLÜ SKOR HESAPLAMA (v2)
# ==========================================

def calculate_dual_score_v2(row, prev_row, market_regime, ls_ratio, sr_data):
    """
    LONG ve SHORT puanı hesapla.
    market_regime: 'BULL', 'BEAR', 'NEUTRAL'
    ls_ratio: Simüle Long/Short oranı
    sr_data: Destek/direnç seviyeleri
    """
    price = float(row['close'])
    
    # === Değerleri al ===
    adx = float(row['adx']) if pd.notna(row['adx']) else 0
    di_plus = float(row['di_plus']) if pd.notna(row['di_plus']) else 0
    di_minus = float(row['di_minus']) if pd.notna(row['di_minus']) else 0
    ema9 = float(row['ema9']) if pd.notna(row['ema9']) else price
    ema21 = float(row['ema21']) if pd.notna(row['ema21']) else price
    ema50 = float(row['ema50']) if pd.notna(row['ema50']) else price
    rsi = float(row['rsi']) if pd.notna(row['rsi']) else 50
    macd_val = float(row['macd']) if pd.notna(row['macd']) else 0
    macd_sig = float(row['macd_signal']) if pd.notna(row['macd_signal']) else 0
    macd_hist = float(row['macd_hist']) if pd.notna(row['macd_hist']) else 0
    bb_pct = float(row['bb_pct']) if pd.notna(row['bb_pct']) else 0.5
    bb_width = float(row['bb_width']) if pd.notna(row['bb_width']) else 0
    stoch_k = float(row['stoch_k']) if pd.notna(row['stoch_k']) else 50
    mfi = float(row['mfi']) if pd.notna(row['mfi']) else 50
    atr = float(row['atr']) if pd.notna(row['atr']) else price * 0.02
    
    ema9_slope = float(row['ema9_slope']) if pd.notna(row['ema9_slope']) else 0
    ema21_slope = float(row['ema21_slope']) if pd.notna(row['ema21_slope']) else 0
    ema50_slope = float(row['ema50_slope']) if pd.notna(row['ema50_slope']) else 0
    
    prev_ema9 = float(prev_row['ema9']) if pd.notna(prev_row['ema9']) else price
    prev_ema21 = float(prev_row['ema21']) if pd.notna(prev_row['ema21']) else price
    prev_macd = float(prev_row['macd']) if pd.notna(prev_row['macd']) else 0
    prev_macd_sig = float(prev_row['macd_signal']) if pd.notna(prev_row['macd_signal']) else 0
    
    vol = float(row['volume']) if pd.notna(row['volume']) else 0
    vol_sma = float(row['vol_sma']) if pd.notna(row['vol_sma']) else vol
    
    # ═══════════════════════════════════════════════════════════════
    # LONG PUANLAMA
    # ═══════════════════════════════════════════════════════════════
    long_score = 0
    long_reasons = []
    long_confirmations = 0  # Kaç farklı indikatör onaylıyor
    
    # 1. EMA Dizilimi + Eğim (25p)
    if price > ema9 > ema21 > ema50:
        if ema9_slope > 0 and ema21_slope > 0:
            long_score += 25
            long_reasons.append("Bullish EMA + yükselen eğim")
            long_confirmations += 1
        else:
            long_score += 15
            long_reasons.append("Bullish EMA (düz eğim)")
            long_confirmations += 1
    elif price > ema21 and ema9 > ema21 and ema9_slope > 0:
        long_score += 12
        long_reasons.append("EMA Bullish")
        long_confirmations += 1
    
    # 2. Golden Cross (20p)
    if prev_ema9 <= prev_ema21 and ema9 > ema21:
        long_score += 20
        long_reasons.append("GOLDEN CROSS")
        long_confirmations += 1
    
    # 3. ADX + DI (20p)
    if adx > 25 and di_plus > di_minus:
        long_score += 20
        long_reasons.append(f"ADX({adx:.0f})+DI+")
        long_confirmations += 1
    elif adx > 20 and di_plus > di_minus * 1.2:
        long_score += 10
        long_reasons.append("DI+>DI-")
    
    # 4. MACD (20p)
    if prev_macd <= prev_macd_sig and macd_val > macd_sig:
        long_score += 20
        long_reasons.append("MACD Cross")
        long_confirmations += 1
    elif macd_val > macd_sig and macd_hist > 0 and macd_hist > float(prev_row['macd_hist'] if pd.notna(prev_row['macd_hist']) else 0):
        long_score += 10
        long_reasons.append("MACD+ artıyor")
        long_confirmations += 1
    
    # 5. RSI — akıllı okuma (15p)
    if rsi < 30:
        # Aşırı satım — bounce potansiyeli AMA eğim kontrolü
        if ema9_slope >= 0:  # Düşüş durmuş mu?
            long_score += 15
            long_reasons.append(f"RSI({rsi:.0f}) bounce")
            long_confirmations += 1
        else:
            long_score += 5  # Hala düşüyor, dikkatli
            long_reasons.append(f"RSI({rsi:.0f}) ama düşüşte")
    elif 40 <= rsi <= 60 and ema9_slope > 0:
        long_score += 8
        long_reasons.append(f"RSI({rsi:.0f}) nötr+yükseliş")
    elif 60 < rsi < 70:
        long_score += 5
        long_reasons.append(f"RSI({rsi:.0f}) bullish zone")
    
    # 6. BB — akıllı okuma (15p)
    if bb_pct < 0.05 and bb_width > 0.02:
        # Alt bandın altında VE bantlar dar değil → sıçrama potansiyeli
        long_score += 15
        long_reasons.append(f"BB alt bant bounce (W:{bb_width:.2f})")
        long_confirmations += 1
    elif bb_pct < 0.2 and ema9_slope > 0:
        long_score += 8
        long_reasons.append(f"BB alt bölge + yükseliş")
    
    # 7. StochRSI (10p)
    if stoch_k < 20:
        long_score += 10
        long_reasons.append(f"Stoch({stoch_k:.0f}) aşırı satım")
        long_confirmations += 1
    
    # 8. MFI (5p) 
    if mfi < 25:
        long_score += 5
        long_reasons.append(f"MFI({mfi:.0f})")
    
    # 9. Volume onayı (10p)
    is_green = row['close'] > row['open']
    if vol > vol_sma * 1.5 and is_green:
        long_score += 10
        long_reasons.append("Hacim spike + yeşil")
        long_confirmations += 1
    
    # ═══════════════════════════════════════════════════════════════
    # SHORT PUANLAMA
    # ═══════════════════════════════════════════════════════════════
    short_score = 0
    short_reasons = []
    short_confirmations = 0
    
    # 1. EMA Dizilimi + Eğim (25p)
    if price < ema9 < ema21 < ema50:
        if ema9_slope < 0 and ema21_slope < 0:
            short_score += 25
            short_reasons.append("Bearish EMA + düşen eğim")
            short_confirmations += 1
        else:
            short_score += 15
            short_reasons.append("Bearish EMA (düz eğim)")
            short_confirmations += 1
    elif price < ema21 and ema9 < ema21 and ema9_slope < 0:
        short_score += 12
        short_reasons.append("EMA Bearish")
        short_confirmations += 1
    
    # 2. Death Cross (20p)
    if prev_ema9 >= prev_ema21 and ema9 < ema21:
        short_score += 20
        short_reasons.append("DEATH CROSS")
        short_confirmations += 1
    
    # 3. ADX + DI (20p)
    if adx > 25 and di_minus > di_plus:
        short_score += 20
        short_reasons.append(f"ADX({adx:.0f})+DI-")
        short_confirmations += 1
    elif adx > 20 and di_minus > di_plus * 1.2:
        short_score += 10
        short_reasons.append("DI->DI+")
    
    # 4. MACD (20p)
    if prev_macd >= prev_macd_sig and macd_val < macd_sig:
        short_score += 20
        short_reasons.append("MACD Bearish Cross")
        short_confirmations += 1
    elif macd_val < macd_sig and macd_hist < 0 and macd_hist < float(prev_row['macd_hist'] if pd.notna(prev_row['macd_hist']) else 0):
        short_score += 10
        short_reasons.append("MACD- derinleşiyor")
        short_confirmations += 1
    
    # 5. RSI (15p)
    if rsi > 80:
        if ema9_slope <= 0:  # Yükseliş durmuş mu?
            short_score += 15
            short_reasons.append(f"RSI({rsi:.0f}) aşırı alım + dönüş")
            short_confirmations += 1
        else:
            short_score += 5
            short_reasons.append(f"RSI({rsi:.0f}) aşırı alım ama trend güçlü")
    elif 40 < rsi <= 60 and ema9_slope < 0:
        short_score += 8
        short_reasons.append(f"RSI({rsi:.0f}) nötr+düşüş")
    elif 30 < rsi < 40:
        short_score += 5
        short_reasons.append(f"RSI({rsi:.0f}) bearish zone")
    
    # 6. BB (15p)
    if bb_pct > 0.95 and bb_width > 0.02:
        short_score += 15
        short_reasons.append(f"BB üst bant red (W:{bb_width:.2f})")
        short_confirmations += 1
    elif bb_pct > 0.8 and ema9_slope < 0:
        short_score += 8
        short_reasons.append(f"BB üst bölge + düşüş")
    
    # 7. StochRSI (10p)
    if stoch_k > 85:
        short_score += 10
        short_reasons.append(f"Stoch({stoch_k:.0f}) aşırı alım")
        short_confirmations += 1
    
    # 8. MFI (5p)
    if mfi > 80:
        short_score += 5
        short_reasons.append(f"MFI({mfi:.0f})")
    
    # 9. Volume onayı (10p)
    is_red = row['close'] < row['open']
    if vol > vol_sma * 1.5 and is_red:
        short_score += 10
        short_reasons.append("Hacim spike + kırmızı")
        short_confirmations += 1
    
    # ═══════════════════════════════════════════════════════════════
    # DESTEK / DİRENÇ BONUSU
    # ═══════════════════════════════════════════════════════════════
    if sr_data:
        sr_bonus_long, sr_reasons_long = check_sr_quality(price, 'LONG', sr_data, atr)
        sr_bonus_short, sr_reasons_short = check_sr_quality(price, 'SHORT', sr_data, atr)
        
        long_score += sr_bonus_long
        long_reasons.extend(sr_reasons_long)
        
        short_score += sr_bonus_short
        short_reasons.extend(sr_reasons_short)
    
    # ═══════════════════════════════════════════════════════════════
    # MARKET REJİMİ AĞIRLANDIRMASI
    # ═══════════════════════════════════════════════════════════════
    
    if market_regime == 'BULL':
        long_score += 20
        long_reasons.append("₿ BTC BULL (+20)")
        short_score -= 25
        short_reasons.append("₿ BTC BULL (short ceza -25)")
    elif market_regime == 'BEAR':
        # ★ BEAR = SHORT ANA SİLAH - ağırlık güçlendirildi
        short_score += 30
        short_reasons.append("₿ BTC BEAR (+30)")
        long_score -= 40
        long_reasons.append("₿ BTC BEAR (long ceza -40)")
    
    # L/S Ratio etkisi
    if ls_ratio > 1.3:
        long_score += 5
        long_reasons.append(f"L/S={ls_ratio:.2f} long ağırlıklı")
    elif ls_ratio < 0.7:
        short_score += 5
        short_reasons.append(f"L/S={ls_ratio:.2f} short ağırlıklı")
    
    # ═══════════════════════════════════════════════════════════════
    # YÖN BELİRLE
    # ═══════════════════════════════════════════════════════════════
    direction = None
    score = 0
    reasons = []
    confirmations = 0
    
    # KURAL 1: Rejime gore agresif yon filtreleme
    if market_regime == 'BEAR':
        # ★ BEAR: SHORT ANA SİLAH - öncelikli yön
        short_threshold = SCORE_THRESHOLD       # 60 - kalite esigi (55'ten yukari)
        short_min_conf = 3                       # 3 onay (daha kaliteli giris)
        long_threshold = 95                      # LONG neredeyse imkansiz
        long_min_conf = 6                        # 6 onay - cok zor
    elif market_regime == 'BULL':
        # BULL: LONG kolay, SHORT cok zor
        long_threshold = SCORE_THRESHOLD - 5    # 55
        long_min_conf = 2
        short_threshold = 90
        short_min_conf = 5
    else:
        # NEUTRAL: Her iki yon icin yuksek esik
        long_threshold = SCORE_THRESHOLD + 10   # 70
        long_min_conf = 3
        short_threshold = SCORE_THRESHOLD + 10   # 70
        short_min_conf = 3
    
    # KURAL 2: Rejime gore yon sec
    if market_regime == 'BEAR':
        # ★ BEAR: SHORT ONCELIKLI - LONG'u yenmesi gerekmiyor
        if short_score >= short_threshold and short_confirmations >= short_min_conf:
            direction = 'SHORT'
            score = short_score
            reasons = short_reasons
            confirmations = short_confirmations
        elif long_score >= long_threshold and long_confirmations >= long_min_conf:
            # SHORT yoksa VE LONG cok guclu ise (95+, 6 onay)
            direction = 'LONG'
            score = long_score
            reasons = long_reasons
            confirmations = long_confirmations
    elif market_regime == 'BULL':
        # BULL: LONG ONCELIKLI
        if long_score >= long_threshold and long_confirmations >= long_min_conf:
            direction = 'LONG'
            score = long_score
            reasons = long_reasons
            confirmations = long_confirmations
        elif short_score >= short_threshold and short_confirmations >= short_min_conf:
            direction = 'SHORT'
            score = short_score
            reasons = short_reasons
            confirmations = short_confirmations
    else:
        # NEUTRAL: En yuksek skora gore
        if long_score > short_score and long_score >= long_threshold:
            if long_confirmations >= long_min_conf:
                direction = 'LONG'
                score = long_score
                reasons = long_reasons
                confirmations = long_confirmations
        if short_score > long_score and short_score >= short_threshold:
            if short_confirmations >= short_min_conf:
                direction = 'SHORT'
                score = short_score
                reasons = short_reasons
                confirmations = short_confirmations
    
    return direction, score, reasons, long_score, short_score, confirmations


# ==========================================
# � GİRİŞ ÖNCESİ DERİN DOĞRULAMA
# ==========================================

def pre_entry_validation(row, prev_row, direction, sr_data, df, idx):
    """
    İşleme girmeden ÖNCE tüm indikatörleri, mum yapısını, hacmi,
    destek/direnci ve Bollinger bantlarını detaylı kontrol et.
    Returns: (geçti: bool, kalite_puanı: int, red_sebepleri: list)
    """
    price = float(row['close'])
    open_p = float(row['open'])
    high = float(row['high'])
    low = float(row['low'])
    rsi = float(row['rsi']) if pd.notna(row['rsi']) else 50
    macd_val = float(row['macd']) if pd.notna(row['macd']) else 0
    macd_sig = float(row['macd_signal']) if pd.notna(row['macd_signal']) else 0
    macd_hist = float(row['macd_hist']) if pd.notna(row['macd_hist']) else 0
    adx = float(row['adx']) if pd.notna(row['adx']) else 0
    di_plus = float(row['di_plus']) if pd.notna(row['di_plus']) else 0
    di_minus = float(row['di_minus']) if pd.notna(row['di_minus']) else 0
    bb_pct = float(row['bb_pct']) if pd.notna(row['bb_pct']) else 0.5
    bb_upper = float(row['bb_upper']) if pd.notna(row['bb_upper']) else price * 1.02
    bb_lower = float(row['bb_lower']) if pd.notna(row['bb_lower']) else price * 0.98
    bb_width = float(row['bb_width']) if pd.notna(row['bb_width']) else 0
    stoch_k = float(row['stoch_k']) if pd.notna(row['stoch_k']) else 50
    mfi = float(row['mfi']) if pd.notna(row['mfi']) else 50
    atr = float(row['atr']) if pd.notna(row['atr']) else price * 0.02
    vol = float(row['volume']) if pd.notna(row['volume']) else 0
    vol_sma = float(row['vol_sma']) if pd.notna(row['vol_sma']) else vol
    ema9 = float(row['ema9']) if pd.notna(row['ema9']) else price
    ema21 = float(row['ema21']) if pd.notna(row['ema21']) else price
    ema50 = float(row['ema50']) if pd.notna(row['ema50']) else price
    ema9_slope = float(row['ema9_slope']) if pd.notna(row['ema9_slope']) else 0
    
    red_flags = []
    quality = 0  # Kalite puanı: ne kadar yüksekse o kadar güvenli
    
    # ═══ 1. RSI KONTROLÜ ═══
    if direction == 'LONG':
        if rsi > 75:
            red_flags.append(f"RSI({rsi:.0f}) aşırı alım - LONG riskli")
        elif rsi > 65:
            quality -= 5  # Dikkat
        elif 30 < rsi < 50:
            quality += 10  # İdeal bounce zone
        elif rsi <= 30:
            quality += 15  # Aşırı satım bounce
    else:  # SHORT
        if rsi < 25:
            red_flags.append(f"RSI({rsi:.0f}) aşırı satım - SHORT riskli")
        elif rsi < 35:
            quality -= 5
        elif 50 < rsi < 70:
            quality += 10  # İdeal short zone
        elif rsi >= 80:
            quality += 15  # Aşırı alım dönüş
    
    # ═══ 2. MACD KONTROLÜ ═══
    if direction == 'LONG':
        if macd_val < macd_sig and macd_hist < 0:
            # MACD bearish ama LONG'a giriyoruz - histogram azalıyorsa ok
            prev_hist = float(prev_row['macd_hist']) if pd.notna(prev_row['macd_hist']) else 0
            if macd_hist < prev_hist:  # Daha da kötüleşiyor
                red_flags.append("MACD bearish ve kötüleşiyor")
            else:
                quality -= 5
        elif macd_val > macd_sig and macd_hist > 0:
            quality += 10
    else:  # SHORT
        if macd_val > macd_sig and macd_hist > 0:
            prev_hist = float(prev_row['macd_hist']) if pd.notna(prev_row['macd_hist']) else 0
            if macd_hist > prev_hist:
                red_flags.append("MACD bullish ve güçleniyor")
            else:
                quality -= 5
        elif macd_val < macd_sig and macd_hist < 0:
            quality += 10
    
    # ═══ 3. ADX + DI KONTROLÜ ═══
    if adx < 15:
        red_flags.append(f"ADX({adx:.0f}) çok düşük - trend yok, whipsaw riski")
    elif adx > 20:
        if direction == 'LONG' and di_minus > di_plus * 1.3:
            red_flags.append(f"ADX trend var ama DI- baskın ({di_minus:.0f}>{di_plus:.0f})")
        elif direction == 'SHORT' and di_plus > di_minus * 1.3:
            red_flags.append(f"ADX trend var ama DI+ baskın ({di_plus:.0f}>{di_minus:.0f})")
        else:
            quality += 10
    
    # ═══ 4. BOLLINGER BANT KONTROLÜ ═══
    if bb_width < 0.015:
        red_flags.append(f"BB çok dar ({bb_width:.3f}) - sıkışma, yön belirsiz")
    
    if direction == 'LONG':
        if bb_pct > 0.95:
            red_flags.append(f"BB üst bandında({bb_pct:.2f}) - LONG tehlikeli")
        elif bb_pct < 0.2:
            quality += 10  # Alt bant yakını, bounce potansiyeli
    else:  # SHORT
        if bb_pct < 0.05:
            red_flags.append(f"BB alt bandında({bb_pct:.2f}) - SHORT tehlikeli")
        elif bb_pct > 0.8:
            quality += 10  # Üst bant yakını, düşüş potansiyeli
    
    # ═══ 5. DESTEK/DİRENÇ KONTROLÜ ═══
    if sr_data:
        support = sr_data['nearest_support']
        resistance = sr_data['nearest_resistance']
        pivot = sr_data['pivot']
        
        if direction == 'LONG':
            dist_to_resistance = (resistance - price) / atr if atr > 0 else 0
            dist_to_support = (price - support) / atr if atr > 0 else 0
            
            if dist_to_resistance < 0.5:
                red_flags.append(f"Direnç çok yakın ({dist_to_resistance:.1f}ATR) - yukarı alan yok")
            elif dist_to_resistance >= 2.0:
                quality += 10  # Yukarı alan bol
            
            if dist_to_support < 0.3:
                quality += 5  # Destekte, bounce
            
            # Pivot üstünde mi?
            if price > pivot:
                quality += 5
        
        else:  # SHORT
            dist_to_support = (price - support) / atr if atr > 0 else 0
            dist_to_resistance = (resistance - price) / atr if atr > 0 else 0
            
            if dist_to_support < 0.5:
                red_flags.append(f"Destek çok yakın ({dist_to_support:.1f}ATR) - aşağı alan yok")
            elif dist_to_support >= 2.0:
                quality += 10
            
            if dist_to_resistance < 0.3:
                quality += 5  # Dirençte, düşüş
            
            if price < pivot:
                quality += 5
    
    # ═══ 6. HACİM KONTROLÜ ═══
    if vol_sma > 0:
        vol_ratio = vol / vol_sma
        if vol_ratio < 0.3:
            red_flags.append(f"Hacim çok düşük ({vol_ratio:.1f}x) - sahte sinyal riski")
        elif vol_ratio < 0.6:
            quality -= 10  # Düşük hacim
        elif vol_ratio > 1.5:
            # Yüksek hacim - yön uyumu kontrol et
            is_green = price > open_p
            if direction == 'LONG' and is_green:
                quality += 15  # Yüksek hacimli yeşil - güçlü sinyal
            elif direction == 'SHORT' and not is_green:
                quality += 15  # Yüksek hacimli kırmızı - güçlü sinyal
            elif direction == 'LONG' and not is_green:
                red_flags.append("Yüksek hacim ama kırmızı mum - LONG riskli")
            elif direction == 'SHORT' and is_green:
                red_flags.append("Yüksek hacim ama yeşil mum - SHORT riskli")
        elif vol_ratio > 1.0:
            quality += 5
    
    # ═══ 7. MUM YAPISI ANALİZİ ═══
    body = abs(price - open_p)
    total_range = high - low if high > low else 0.0001
    body_ratio = body / total_range
    upper_wick = high - max(price, open_p)
    lower_wick = min(price, open_p) - low
    
    # Doji mum (kararsızlık)
    if body_ratio < 0.1:
        quality -= 10  # Kararsızlık mumunda girme
    
    if direction == 'LONG':
        # Uzun alt fitil = alıcılar var
        if lower_wick > body * 2 and price > open_p:
            quality += 10  # Hammer/Pin bar
        # Uzun üst fitil = satıcılar güçlü
        if upper_wick > body * 2 and price < open_p:
            red_flags.append("Uzun üst fitil - satış baskısı")
    else:  # SHORT
        # Uzun üst fitil = satıcılar var
        if upper_wick > body * 2 and price < open_p:
            quality += 10  # Shooting star
        # Uzun alt fitil = alıcılar güçlü  
        if lower_wick > body * 2 and price > open_p:
            red_flags.append("Uzun alt fitil - alım baskısı")
    
    # ═══ 8. SON 3 MUMUN TREND KONTROLÜ ═══
    if idx >= 3:
        last3_green = sum(1 for j in range(idx-2, idx+1) if df.iloc[j]['close'] > df.iloc[j]['open'])
        if direction == 'LONG' and last3_green == 0:
            red_flags.append("Son 3 mum kırmızı - LONG için hala erken")
        elif direction == 'SHORT' and last3_green == 3:
            red_flags.append("Son 3 mum yeşil - SHORT için hala erken")
        elif direction == 'LONG' and last3_green >= 2:
            quality += 5
        elif direction == 'SHORT' and last3_green <= 1:
            quality += 5
    
    # ═══ 9. EMA SLOPE UYUMU ═══
    if direction == 'LONG' and ema9_slope < -0.5:
        red_flags.append(f"EMA9 düşüşte ({ema9_slope:.2f}%) - momentum yok")
    elif direction == 'SHORT' and ema9_slope > 0.5:
        red_flags.append(f"EMA9 yükselişte ({ema9_slope:.2f}%) - momentum ters")
    
    # ═══ 10. STOCHRSI + MFI UYUMU ═══
    if direction == 'LONG':
        if stoch_k > 90 and mfi > 80:
            red_flags.append("StochRSI + MFI ikisi de aşırı alım")
    else:
        if stoch_k < 10 and mfi < 20:
            red_flags.append("StochRSI + MFI ikisi de aşırı satım")
    
    # ═══ SONUÇ ═══
    # 2+ red flag varsa girme, 1 red flag varsa quality -20
    if len(red_flags) >= 2:
        return False, quality, red_flags
    elif len(red_flags) == 1:
        quality -= 20
    
    # Minimum kalite eşiği
    if quality < -10:
        red_flags.append(f"Kalite puanı çok düşük ({quality})")
        return False, quality, red_flags
    
    return True, quality, red_flags


# ==========================================
# �🔄 BACKTEST FONKSİYONU (v2)
# ==========================================

def backtest_coin(symbol, df, btc_regimes, btc_timestamps):
    """Tek coin için geliştirilmiş backtest."""
    trades = []
    in_position = False
    position_direction = None
    entry_price = 0
    entry_time = None
    entry_candle_idx = 0
    stop_loss = 0
    original_stop = 0
    tp1 = tp2 = tp3 = 0
    tp1_hit = tp2_hit = False
    position_remaining = 1.0
    last_exit_candle = -999
    trade_count = 0
    leverage = 5
    
    # --- YANLIŞ SİNYAL TAKİBİ ---
    wrong_signal_bans = defaultdict(set)
    daily_win_streak = defaultdict(int)
    
    # --- COIN TIER ---
    coin_tier = get_coin_tier(symbol)
    
    # --- COIN BAZLI KAYIP TAKIBI ---
    consecutive_losses = 0           # Ust uste kayip sayisi
    coin_banned = False              # MAX_CONSECUTIVE_LOSSES_COIN asildi mi
    last_loss_candle = -999          # Son kayip mumu
    
    # --- DINAMIK MAX LOSS (pozisyon bazli, giris aninda set edilir) ---
    trade_max_loss = MAX_LOSS_PER_TRADE_PCT  # Default, her giriste guncellenir
    
    def track_exit_result(pnl_pct_val, tp1_was_hit):
        """Her cikista kayip/kazanc takibi yap."""
        nonlocal consecutive_losses, coin_banned
        if pnl_pct_val < 0 and not tp1_was_hit:
            # Pure kayip (TP1'e bile ulasmadi)
            consecutive_losses += 1
            if consecutive_losses >= MAX_CONSECUTIVE_LOSSES_COIN:
                coin_banned = True  # Bu coin icin daha fazla islem yok
        elif pnl_pct_val > 0:
            consecutive_losses = 0  # Kazanc dizisi sifirla
    
    # Volatilite kontrolü
    if len(df) > 50:
        first_atr = df.iloc[50]['atr'] if pd.notna(df.iloc[50]['atr']) else 0
        first_price = df.iloc[50]['close']
        atr_pct = (first_atr / first_price) * 100 if first_price > 0 else 0
        if atr_pct > MAX_ATR_PERCENT or atr_pct < MIN_ATR_PERCENT:
            return []
    
    for i in range(51, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        current_price = float(row['close'])
        current_time = row['timestamp']
        high = float(row['high'])
        low = float(row['low'])
        atr = float(row['atr']) if pd.notna(row['atr']) else current_price * 0.02
        current_date = current_time.strftime('%Y-%m-%d')
        
        if in_position:
            # === MAX HOLD SURESI KONTROLU (4 saat = 16 mum) ===
            candles_in_trade = i - entry_candle_idx
            if candles_in_trade >= MAX_HOLD_CANDLES:
                exit_price = current_price
                if position_direction == 'SHORT':
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * position_remaining * leverage
                else:
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100 * position_remaining * leverage
                pnl_pct = max(pnl_pct, trade_max_loss)
                result_text = f'TIMEOUT {candles_in_trade*15}dk'
                if tp1_hit: result_text = f'TIMEOUT (TP1+) {candles_in_trade*15}dk'
                if tp2_hit: result_text = f'TIMEOUT (TP2+) {candles_in_trade*15}dk'
                trades.append({
                    'symbol': symbol, 'direction': position_direction,
                    'entry_time': entry_time, 'exit_time': current_time,
                    'entry_price': entry_price, 'exit_price': exit_price,
                    'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                    'pnl_pct': pnl_pct, 'result': result_text, 'leverage': leverage
                })
                ban_date = current_time.strftime('%Y-%m-%d')
                if pnl_pct < 0 and not tp1_hit:
                    wrong_signal_bans[ban_date].add(position_direction)
                elif pnl_pct > 0:
                    wrong_signal_bans[ban_date].discard(position_direction)
                track_exit_result(pnl_pct, tp1_hit)
                in_position = False
                last_exit_candle = i
                position_remaining = 1.0
                continue
            
            # === BTC ANI HAREKET KONTROLU (pozisyondayken) ===
            btc_regime_now, btc_str_now, btc_ls_now = get_btc_regime_fast(btc_regimes, current_time, btc_timestamps)
            btc_against = False
            if position_direction == 'LONG' and btc_regime_now == 'BEAR' and btc_str_now >= 60:
                btc_against = True
            elif position_direction == 'SHORT' and btc_regime_now == 'BULL' and btc_str_now >= 60:
                btc_against = True
            
            # BTC guclu ters gidiyorsa ve min hold suresi gecmisse, erken cik
            if btc_against and candles_in_trade >= MIN_HOLD_CANDLES and not tp1_hit:
                exit_price = current_price
                if position_direction == 'SHORT':
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * position_remaining * leverage
                else:
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100 * position_remaining * leverage
                pnl_pct = max(pnl_pct, trade_max_loss)
                trades.append({
                    'symbol': symbol, 'direction': position_direction,
                    'entry_time': entry_time, 'exit_time': current_time,
                    'entry_price': entry_price, 'exit_price': exit_price,
                    'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                    'pnl_pct': pnl_pct, 'result': 'BTC TERS', 'leverage': leverage
                })
                ban_date = current_time.strftime('%Y-%m-%d')
                if pnl_pct < 0:
                    wrong_signal_bans[ban_date].add(position_direction)
                elif pnl_pct > 0:
                    wrong_signal_bans[ban_date].discard(position_direction)
                track_exit_result(pnl_pct, tp1_hit)
                in_position = False
                last_exit_candle = i
                position_remaining = 1.0
                continue
            
            # Trailing Stop
            if TRAILING_STOP:
                if position_direction == 'SHORT':
                    if tp1_hit and not tp2_hit:
                        new_stop = entry_price + (original_stop - entry_price) * 0.5
                        if stop_loss > new_stop:
                            stop_loss = new_stop
                    if tp2_hit:
                        if stop_loss > entry_price:
                            stop_loss = entry_price
                else:  # LONG
                    if tp1_hit and not tp2_hit:
                        new_stop = entry_price - (entry_price - original_stop) * 0.5
                        if stop_loss < new_stop:
                            stop_loss = new_stop
                    if tp2_hit:
                        if stop_loss < entry_price:
                            stop_loss = entry_price
            
            # Stop Loss kontrol
            sl_triggered = False
            if position_direction == 'SHORT' and high >= stop_loss:
                sl_triggered = True
                exit_price = stop_loss
            elif position_direction == 'LONG' and low <= stop_loss:
                sl_triggered = True
                exit_price = stop_loss
            
            if sl_triggered:
                if position_direction == 'SHORT':
                    pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * position_remaining * leverage
                else:
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100 * position_remaining * leverage
                
                # MAX KAYIP LİMİTİ (dinamik - volatiliteye gore)
                pnl_pct = max(pnl_pct, trade_max_loss)
                
                result_text = 'STOP LOSS'
                if tp1_hit: result_text = 'TRAILING (TP1+)'
                if tp2_hit: result_text = 'TRAILING (TP2+)'

                trades.append({
                    'symbol': symbol, 'direction': position_direction,
                    'entry_time': entry_time, 'exit_time': current_time,
                    'entry_price': entry_price, 'exit_price': exit_price,
                    'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                    'pnl_pct': pnl_pct, 'result': result_text, 'leverage': leverage
                })
                
                # YANLIS SINYAL TAKIBI
                ban_date = current_time.strftime('%Y-%m-%d')
                if pnl_pct < 0 and not tp1_hit:
                    # Pure stop loss (TP1'e bile gelmedi) → sadece O YÖNÜ banla
                    wrong_signal_bans[ban_date].add(position_direction)
                    daily_win_streak[ban_date] = 0
                elif pnl_pct > 0:
                    # Kazandık → banı kaldır, devam et! 
                    # O yön kazanıyor demek, tekrar girilebilir
                    wrong_signal_bans[ban_date].discard(position_direction)
                    daily_win_streak[ban_date] = daily_win_streak.get(ban_date, 0) + 1
                
                track_exit_result(pnl_pct, tp1_hit)
                in_position = False
                last_exit_candle = i
                position_remaining = 1.0
                continue
            
            # Partial TP
            if PARTIAL_TP:
                if position_direction == 'SHORT':
                    if not tp1_hit and low <= tp1:
                        tp1_hit = True
                        partial_pnl = ((entry_price - tp1) / entry_price) * 100 * TP1_CLOSE_PCT * leverage
                        trades.append({
                            'symbol': symbol, 'direction': position_direction,
                            'entry_time': entry_time, 'exit_time': current_time,
                            'entry_price': entry_price, 'exit_price': tp1,
                            'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                            'pnl_pct': partial_pnl, 'result': 'TP1', 'leverage': leverage
                        })
                        position_remaining = 1.0 - TP1_CLOSE_PCT
                    
                    if tp1_hit and not tp2_hit and low <= tp2:
                        tp2_hit = True
                        partial_pnl = ((entry_price - tp2) / entry_price) * 100 * TP2_CLOSE_PCT * leverage
                        trades.append({
                            'symbol': symbol, 'direction': position_direction,
                            'entry_time': entry_time, 'exit_time': current_time,
                            'entry_price': entry_price, 'exit_price': tp2,
                            'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                            'pnl_pct': partial_pnl, 'result': 'TP2', 'leverage': leverage
                        })
                        position_remaining = TP3_CLOSE_PCT
                    
                    if tp2_hit and low <= tp3:
                        partial_pnl = ((entry_price - tp3) / entry_price) * 100 * TP3_CLOSE_PCT * leverage
                        trades.append({
                            'symbol': symbol, 'direction': position_direction,
                            'entry_time': entry_time, 'exit_time': current_time,
                            'entry_price': entry_price, 'exit_price': tp3,
                            'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                            'pnl_pct': partial_pnl, 'result': 'TP3', 'leverage': leverage
                        })
                        track_exit_result(partial_pnl, True)
                        in_position = False
                        last_exit_candle = i
                        position_remaining = 1.0
                        continue
                
                else:  # LONG
                    if not tp1_hit and high >= tp1:
                        tp1_hit = True
                        partial_pnl = ((tp1 - entry_price) / entry_price) * 100 * TP1_CLOSE_PCT * leverage
                        trades.append({
                            'symbol': symbol, 'direction': position_direction,
                            'entry_time': entry_time, 'exit_time': current_time,
                            'entry_price': entry_price, 'exit_price': tp1,
                            'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                            'pnl_pct': partial_pnl, 'result': 'TP1', 'leverage': leverage
                        })
                        position_remaining = 1.0 - TP1_CLOSE_PCT
                    
                    if tp1_hit and not tp2_hit and high >= tp2:
                        tp2_hit = True
                        partial_pnl = ((tp2 - entry_price) / entry_price) * 100 * TP2_CLOSE_PCT * leverage
                        trades.append({
                            'symbol': symbol, 'direction': position_direction,
                            'entry_time': entry_time, 'exit_time': current_time,
                            'entry_price': entry_price, 'exit_price': tp2,
                            'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                            'pnl_pct': partial_pnl, 'result': 'TP2', 'leverage': leverage
                        })
                        position_remaining = TP3_CLOSE_PCT
                    
                    if tp2_hit and high >= tp3:
                        partial_pnl = ((tp3 - entry_price) / entry_price) * 100 * TP3_CLOSE_PCT * leverage
                        trades.append({
                            'symbol': symbol, 'direction': position_direction,
                            'entry_time': entry_time, 'exit_time': current_time,
                            'entry_price': entry_price, 'exit_price': tp3,
                            'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                            'pnl_pct': partial_pnl, 'result': 'TP3', 'leverage': leverage
                        })
                        track_exit_result(partial_pnl, True)
                        in_position = False
                        last_exit_candle = i
                        position_remaining = 1.0
                        continue
        else:
            # === Yeni pozisyon aç ===
            # Coin banliysa hic girme
            if coin_banned:
                continue
            
            # Cooldown kontrolu (kayiptan sonra daha uzun)
            cooldown = COOLDOWN_AFTER_LOSS if consecutive_losses > 0 else COOLDOWN_CANDLES
            if i - last_exit_candle < cooldown:
                continue
            if trade_count >= MAX_TRADES_PER_COIN:
                continue
            
            # BTC market rejimi al
            market_regime, regime_strength, ls_ratio = get_btc_regime_fast(btc_regimes, current_time, btc_timestamps)
            
            # Destek/Direnç hesapla (son 96 mum = 24 saat)
            sr_data = calculate_support_resistance(df.iloc[max(0,i-96):i+1], lookback=96)
            
            # Skor hesapla
            direction, score, reasons, long_sc, short_sc, confirmations = \
                calculate_dual_score_v2(row, prev_row, market_regime, ls_ratio, sr_data)
            
            if direction is None:
                continue
            
            # YANLIŞ SİNYAL BAN KONTROLÜ
            if current_date in wrong_signal_bans:
                if direction in wrong_signal_bans[current_date]:
                    continue  # O gün kaybettik, her iki yönde de ban var
            
            # Win rate hesapla
            win_rate = 55
            if score >= 90: win_rate += 15
            elif score >= 75: win_rate += 10
            elif score >= 60: win_rate += 5
            
            # Onay sayısı bonusu
            if confirmations >= 5: win_rate += 15
            elif confirmations >= 4: win_rate += 10
            elif confirmations >= 3: win_rate += 5
            
            # Market uyum bonusu
            if (direction == 'LONG' and market_regime == 'BULL') or \
               (direction == 'SHORT' and market_regime == 'BEAR'):
                win_rate += 10
            
            if score >= SCORE_THRESHOLD and win_rate >= MIN_WIN_RATE:
                # ══════ GİRİŞ ÖNCESİ DERİN DOĞRULAMA ══════
                passed, quality, red_flags = pre_entry_validation(
                    row, prev_row, direction, sr_data, df, i
                )
                if not passed:
                    continue  # Doğrulama geçemedi, girme
                
                # Kaliteye göre win_rate bonusu  
                if quality >= 30:
                    win_rate += 10
                elif quality >= 15:
                    win_rate += 5
                
                # 24h USD HACIM KONTROLU - min 20M
                vol_usd_24h = float(row['vol_usd_24h']) if pd.notna(row.get('vol_usd_24h', None)) else 0
                if vol_usd_24h < MIN_24H_VOLUME_USD:
                    continue  # Hacim yetersiz, girme
                
                # BTC YON UYUMU KONTROLU (giris aninda)
                if (direction == 'LONG' and market_regime == 'BEAR' and regime_strength >= 30):
                    continue  # BTC duserken LONG acma (esik 30'a dusuruldu - daha agresif)
                if (direction == 'SHORT' and market_regime == 'BULL' and regime_strength >= 40):
                    continue  # BTC yukselirken SHORT acma
                
                # ★ BEAR SHORT GIRIS ZAMANLAMA KONTROLU
                if direction == 'SHORT' and market_regime == 'BEAR':
                    ema9_slope_val = float(row['ema9_slope']) if pd.notna(row['ema9_slope']) else 0
                    ema21_val = float(row['ema21']) if pd.notna(row['ema21']) else current_price
                    price_to_ema21 = ((current_price - ema21_val) / ema21_val * 100) if ema21_val > 0 else 0
                    
                    # EMA9 hala yukarı gidiyorsa -> momentum ters, short erken
                    if ema9_slope_val > 0.3:
                        continue  # Yukarı momentum devam ediyor, short için bekle
                    
                    # Fiyat EMA21'in %2'den fazla altındaysa -> çok düşmüş, pullback bekle
                    if price_to_ema21 < -2.0:
                        continue  # Zaten düşmüş, geç kaldık, pullback bekleyip daha iyi giriş yap
                
                # ═══ VOLATILITE + COIN TIER KONTROLLERI ═══
                vol_class, avg_atr_pct = get_coin_volatility_class(df, i, lookback=20)
                
                # Volatil piyasa + kucuk coin -> ek skor gereksinimi
                score_penalty = get_volatility_score_penalty(vol_class, coin_tier, regime_strength)
                if score_penalty > 0 and score < (SCORE_THRESHOLD + score_penalty):
                    continue  # Skor yetersiz, volatil ortamda kucuk coin icin daha yuksek skor gerek
                
                # EXTREME volatilite kontrolu
                if vol_class == 'EXTREME' and coin_tier == 'SMALL':
                    continue  # Extreme vol + small coin = kesinlikle girme
                
                in_position = True
                position_direction = direction
                entry_price = current_price
                entry_time = current_time
                entry_candle_idx = i
                trade_count += 1
                
                # Dinamik kaldirac (volatilite ve tier'a gore sinirli)
                leverage = get_leverage(score, win_rate, market_regime, regime_strength, confirmations, direction, vol_class, coin_tier)
                
                # Dinamik max kayip (volatil coinlerde daha siki)
                trade_max_loss = get_dynamic_max_loss(vol_class, coin_tier)
                
                # Dinamik SL carpani (volatil coinlerde daha siki)
                dynamic_sl_mult = get_dynamic_sl_mult(vol_class, coin_tier)
                risk = atr * dynamic_sl_mult
                
                # S/R bazlı SL ayarı - destek/direnç seviyelerine göre akıllı SL
                if direction == 'LONG':
                    base_stop = entry_price - risk
                    sr_stop = sr_data['nearest_support'] - atr * 0.3
                    
                    # Swing low'ları da kontrol et
                    if sr_data['swing_lows']:
                        nearest_swing_low = max([s for s in sr_data['swing_lows'] if s < current_price], default=None)
                        if nearest_swing_low:
                            swing_stop = nearest_swing_low - atr * 0.2
                            original_stop = max(base_stop, sr_stop, swing_stop)
                        else:
                            original_stop = max(base_stop, sr_stop)
                    else:
                        original_stop = max(base_stop, sr_stop)
                    
                    stop_loss = original_stop
                    tp1 = entry_price + (risk * TP1_RR)
                    tp2 = entry_price + (risk * TP2_RR)
                    tp3 = entry_price + (risk * TP3_RR)
                    
                    # TP'yi dirence göre ayarla
                    if sr_data['nearest_resistance'] < tp1:
                        tp1 = sr_data['nearest_resistance'] * 0.998  # Direncin hemen altı
                    
                else:  # SHORT
                    base_stop = entry_price + risk
                    sr_stop = sr_data['nearest_resistance'] + atr * 0.3
                    
                    if sr_data['swing_highs']:
                        nearest_swing_high = min([s for s in sr_data['swing_highs'] if s > current_price], default=None)
                        if nearest_swing_high:
                            swing_stop = nearest_swing_high + atr * 0.2
                            original_stop = min(base_stop, sr_stop, swing_stop)
                        else:
                            original_stop = min(base_stop, sr_stop)
                    else:
                        original_stop = min(base_stop, sr_stop)
                    
                    stop_loss = original_stop
                    tp1 = entry_price - (risk * TP1_RR)
                    tp2 = entry_price - (risk * TP2_RR)
                    tp3 = entry_price - (risk * TP3_RR)
                    
                    if sr_data['nearest_support'] > tp1:
                        tp1 = sr_data['nearest_support'] * 1.002  # Desteğin hemen üstü
                
                tp1_hit = tp2_hit = False
                position_remaining = 1.0
                
                # Signal kaydet
                if not hasattr(backtest_coin, 'signals'):
                    backtest_coin.signals = []
                backtest_coin.signals.append({
                    'symbol': symbol, 'direction': direction,
                    'entry_time': entry_time, 'entry_price': entry_price,
                    'stop_loss': stop_loss, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                    'score': score, 'win_rate': win_rate, 'leverage': leverage,
                    'market_regime': market_regime,
                    'confirmations': confirmations,
                    'vol_class': vol_class, 'coin_tier': coin_tier,
                    'reasons': ' | '.join(reasons)
                })
    
    # Açık pozisyonu kapat
    if in_position:
        last_row = df.iloc[-1]
        exit_price = float(last_row['close'])
        if position_direction == 'SHORT':
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * position_remaining * leverage
        else:
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100 * position_remaining * leverage
        
        pnl_pct = max(pnl_pct, trade_max_loss)
        
        trades.append({
            'symbol': symbol, 'direction': position_direction,
            'entry_time': entry_time, 'exit_time': last_row['timestamp'],
            'entry_price': entry_price, 'exit_price': exit_price,
            'stop_loss': original_stop, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
            'pnl_pct': pnl_pct, 'result': 'CLOSE (End)', 'leverage': leverage
        })
    
    return trades


# ==========================================
# ANA FONKSIYON
# ==========================================

def run_backtest():
    hdr = "=" * 90
    sep = "-" * 90
    print(hdr)
    print("  SWING BACKTEST v2 - GERCEK PORTFOY SIMULASYONU")
    print(hdr)
    print(f"  Tarih       : {BACKTEST_START.strftime('%Y-%m-%d %A')} -> {BACKTEST_END.strftime('%Y-%m-%d %A')}")
    print(f"  Baslangic   : ${INITIAL_BALANCE}")
    print(f"  Pozisyon    : Bakiyenin %{POSITION_SIZE_PCT}'i (4'e bolunmus)")
    print(f"  Kaldirac    : 5x-10x (dinamik, BTC gucune gore)")
    print(f"  Max Kayip   : Dinamik (%10-%20, volatiliteye gore)")
    print(f"  Min Onay    : {MIN_CONFIRMATION_COUNT} indikator")
    print(f"  Esanli Max  : {MAX_CONCURRENT} pozisyon")
    print(f"  Islem Suresi: {MIN_HOLD_CANDLES*15}dk - {MAX_HOLD_CANDLES*15}dk (30dk-4saat)")
    print(f"  Min Hacim   : ${MIN_24H_VOLUME_USD/1e6:.0f}M USD (24h)")
    print(f"  BTC Takip   : Her mumda aktif (ters giderse erken cikis)")
    print(f"  Dogrulama   : 10 asamali derin giris kontrolu aktif")
    print(f"  Coin Tier   : TOP(ilk50)/MID/SMALL - volatil coinlerde kaldirac sinirli")
    print(f"  Volatilite  : ATR bazli dinamik SL, kaldirac ve max kayip")
    print(hdr)
    
    # BTC verisini yukle
    print("\n  [BTC] Veri yukleniyor...")
    btc_df = load_btc_data()
    btc_regimes = {}
    btc_timestamps = np.array([])
    if btc_df is not None:
        print(f"  [OK]  {len(btc_df)} mum yuklendi ({btc_df['timestamp'].min()} - {btc_df['timestamp'].max()})")
        
        print("  [..] BTC rejimleri hesaplaniyor...")
        btc_regimes = precompute_btc_regimes(btc_df)
        btc_timestamps = np.array(sorted(btc_regimes.keys()))
        print(f"  [OK]  {len(btc_regimes)} rejim noktasi hesaplandi")
        
        mid_time = BACKTEST_START + (BACKTEST_END - BACKTEST_START) / 2
        regime, strength, ls = get_btc_regime_fast(btc_regimes, mid_time, btc_timestamps)
        print(f"  [BTC] Orta nokta rejimi: {regime} (Guc: {strength}, L/S: {ls:.2f})")
    else:
        print("  [!!]  BTC verisi yok, trend analizi devre disi")
    
    # CSV dosyalarini bul
    csv_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv') and not f.startswith('_')]
    
    if SINGLE_COIN:
        safe_symbol = SINGLE_COIN.replace('/', '_').replace(':', '_')
        csv_files = [f for f in csv_files if safe_symbol in f]
    
    print(f"\n  [i]  {len(csv_files)} coin bulundu.")
    print("  [..] Tum coinler icin sinyaller hesaplaniyor...\n")
    
    # Reset signals
    if hasattr(backtest_coin, 'signals'):
        backtest_coin.signals = []
    
    all_trades = []
    
    for csv_file in csv_files:
        symbol = csv_file.replace('_USDT_USDT.csv', '/USDT:USDT').replace('_', '/')
        if symbol.count('/') > 1:
            symbol = symbol.split('/')[0] + '/USDT:USDT'
        
        filepath = os.path.join(DATA_FOLDER, csv_file)
        
        try:
            df = pd.read_csv(filepath)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df[(df['timestamp'] >= BACKTEST_START) & (df['timestamp'] <= BACKTEST_END)]
            df = df.reset_index(drop=True)
            
            if len(df) < 100:
                continue
            
            df = calculate_indicators(df)
            trades = backtest_coin(symbol, df, btc_regimes, btc_timestamps)
            
            if trades:
                all_trades.extend(trades)
        
        except Exception as e:
            print(f"  [X]  {symbol}: {e}")
    
    print(f"  [i]  Toplam {len(all_trades)} sinyal/trade bulundu tum coinlerden.")
    
    # ==========================================
    # 💰 GERÇEK PORTFÖY SİMÜLASYONU
    # ==========================================
    # Tüm trade'leri zamana göre sırala, sırayla işle
    # Aynı anda sadece 1 pozisyon açık olabilir
    # Her işlem mevcut bakiye ile açılır
    # ==========================================
    
    all_trades_sorted = sorted(all_trades, key=lambda x: x['entry_time'])
    
    balance = float(INITIAL_BALANCE)
    peak_balance = balance
    max_drawdown = 0
    executed_trades = []
    
    # Aktif pozisyonlar: list of {exit_time, slot_amount}
    active_positions = []
    
    # Yanlis sinyal ban takibi (portfoy seviyesinde)
    portfolio_bans = defaultdict(set)  # {date: set(directions)}
    
    print("\n" + hdr)
    print("  PORTFOY SIMULASYONU - Bakiye 4'e Bolunmus")
    print(f"  Baslangic: ${balance:.2f} | Slot basi: ${balance/4:.2f}")
    print(hdr)
    print(f"  {'#':>3} {'Coin':10} {'Yon':5} {'Giris Zamani':>14} {'Cikis Zamani':>14} {'Lev':>3} {'Slot$':>7} {'Giris':>12} {'Cikis':>12} {'SL':>12} {'TP1':>12} {'TP2':>12} {'TP3':>12} {'PnL%':>7} {'PnL$':>8} {'Bakiye':>9} {'Sonuc'}")
    print(sep)
    
    trade_no = 0
    for trade in all_trades_sorted:
        # Bakiye bittiyse dur
        if balance <= 5:
            print(f"\n  [!!] BAKIYE BITTI: ${balance:.2f} - dur!")
            break
        
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        trade_date = entry_time.strftime('%Y-%m-%d')
        
        # Kapanmis pozisyonlari temizle
        active_positions = [p for p in active_positions if p['exit_time'] > entry_time]
        
        # Max es zamanli pozisyon kontrolu
        if len(active_positions) >= MAX_CONCURRENT:
            continue
        
        # Portfoy seviyesinde ban kontrolu
        if trade_date in portfolio_bans:
            if trade['direction'] in portfolio_bans[trade_date]:
                continue
        
        # Slot buyuklugu: bakiyenin %25'i
        slot_amount = balance * (POSITION_SIZE_PCT / 100)
        if slot_amount < 2:
            continue  # Minimum $2
        
        pnl_pct = trade['pnl_pct']
        leverage = trade['leverage']
        
        # Gercek $ kazanc/kayip = slot miktari uzerinden
        dollar_change = slot_amount * (pnl_pct / 100)
        new_balance = balance + dollar_change
        
        # Bakiye 0'in altina dusmesin (likidasyon)
        if new_balance < 0:
            dollar_change = -balance
            new_balance = 0
        
        # Trade'i kaydet
        executed_trade = trade.copy()
        executed_trade['balance_before'] = balance
        executed_trade['balance_after'] = new_balance
        executed_trade['dollar_pnl'] = dollar_change
        executed_trade['slot_amount'] = slot_amount
        executed_trades.append(executed_trade)
        
        # Aktif pozisyon olarak ekle
        active_positions.append({'exit_time': exit_time, 'slot_amount': slot_amount})
        
        # Ban kontrolu
        if pnl_pct < 0 and trade['result'] == 'STOP LOSS':
            portfolio_bans[trade_date].add(trade['direction'])
        elif pnl_pct > 0:
            portfolio_bans[trade_date].discard(trade['direction'])
        
        # Bakiyeyi guncelle
        trade_no += 1
        dir_tag = "[L]" if trade['direction'] == 'LONG' else "[S]"
        result_tag = "[+]" if pnl_pct > 0 else "[-]"
        symbol_short = trade['symbol'].split('/')[0]
        # ASCII-safe symbol (Cince karakterler icin)
        try:
            symbol_short.encode('ascii')
        except UnicodeEncodeError:
            symbol_short = ''.join(c if ord(c) < 128 else '?' for c in symbol_short)
        
        # Fiyat formatlama - kucuk fiyatlar icin daha fazla decimal
        def fmt_price(p):
            if p is None or p == 0:
                return '-'.rjust(12)
            if p >= 1000:
                return f"{p:>12,.2f}"
            elif p >= 1:
                return f"{p:>12.4f}"
            elif p >= 0.01:
                return f"{p:>12.6f}"
            else:
                return f"{p:>12.8f}"
        
        sl_val = trade.get('stop_loss', 0)
        tp1_val = trade.get('tp1', 0)
        tp2_val = trade.get('tp2', 0)
        tp3_val = trade.get('tp3', 0)
        
        print(f"  {trade_no:>3} {symbol_short:10} {dir_tag:5} {entry_time.strftime('%m-%d %H:%M'):>14} {exit_time.strftime('%m-%d %H:%M'):>14} {leverage:>3}x ${slot_amount:>6.1f} {fmt_price(trade['entry_price'])} {fmt_price(trade['exit_price'])} {fmt_price(sl_val)} {fmt_price(tp1_val)} {fmt_price(tp2_val)} {fmt_price(tp3_val)} {pnl_pct:>+6.1f}% {result_tag}{abs(dollar_change):>6.2f} ${new_balance:>8.2f} {trade['result']}")
        
        balance = new_balance
        
        # Drawdown takibi
        if balance > peak_balance:
            peak_balance = balance
        dd = ((peak_balance - balance) / peak_balance) * 100 if peak_balance > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd
    
    # === SONUCLAR ===
    print("\n" + hdr)
    print("  PORTFOY SONUCLARI")
    print(hdr)
    
    if executed_trades:
        total_dollar_pnl = balance - INITIAL_BALANCE
        total_pnl_pct = (total_dollar_pnl / INITIAL_BALANCE) * 100
        wins = [t for t in executed_trades if t['dollar_pnl'] > 0]
        losses = [t for t in executed_trades if t['dollar_pnl'] <= 0]
        long_trades = [t for t in executed_trades if t['direction'] == 'LONG']
        short_trades = [t for t in executed_trades if t['direction'] == 'SHORT']
        win_rate = len(wins) / len(executed_trades) * 100 if executed_trades else 0
        
        avg_win_dollar = np.mean([t['dollar_pnl'] for t in wins]) if wins else 0
        avg_loss_dollar = np.mean([t['dollar_pnl'] for t in losses]) if losses else 0
        
        long_dollar = sum(t['dollar_pnl'] for t in long_trades)
        short_dollar = sum(t['dollar_pnl'] for t in short_trades)
        
        print(f"  Baslangic Bakiye  : ${INITIAL_BALANCE:.2f}")
        print(f"  Final Bakiye      : ${balance:.2f}")
        print(f"  Toplam PnL        : ${total_dollar_pnl:+.2f} ({total_pnl_pct:+.1f}%)")
        print(sep)
        print(f"  Islem Sayisi      : {len(executed_trades)}")
        print(f"  Kazanc / Kayip    : {len(wins)} / {len(losses)}  (Win Rate: {win_rate:.1f}%)")
        print(f"  Avg Win / Loss    : ${avg_win_dollar:+.2f} / ${avg_loss_dollar:.2f}")
        print(f"  LONG              : {len(long_trades)} islem (${long_dollar:+.2f})")
        print(f"  SHORT             : {len(short_trades)} islem (${short_dollar:+.2f})")
        print(sep)
        print(f"  Max Drawdown      : {max_drawdown:.1f}%")
        print(f"  Peak Bakiye       : ${peak_balance:.2f}")
        
        # Profit Factor
        gross_profit = sum(t['dollar_pnl'] for t in wins) if wins else 0
        gross_loss = abs(sum(t['dollar_pnl'] for t in losses)) if losses else 1
        pf = gross_profit / gross_loss if gross_loss > 0 else 0
        print(f"  Profit Factor     : {pf:.2f}")
        
        # Gunluk breakdown
        print("\n" + sep)
        print("  GUNLUK BREAKDOWN")
        print(sep)
        daily = defaultdict(lambda: {'trades': 0, 'pnl': 0, 'balance': 0})
        for t in executed_trades:
            day = t['entry_time'].strftime('%Y-%m-%d %A')
            daily[day]['trades'] += 1
            daily[day]['pnl'] += t['dollar_pnl']
            daily[day]['balance'] = t['balance_after']
        
        for day in sorted(daily.keys()):
            d = daily[day]
            day_tag = "[+]" if d['pnl'] >= 0 else "[-]"
            print(f"  {day_tag} {day}: {d['trades']:>2} islem | PnL: ${d['pnl']:>+8.2f} | Bakiye: ${d['balance']:>9.2f}")
        
        # En iyi / en kotu
        best = max(executed_trades, key=lambda x: x['dollar_pnl'])
        worst = min(executed_trades, key=lambda x: x['dollar_pnl'])
        def safe_sym(s):
            n = s.split('/')[0]
            try:
                n.encode('ascii')
                return n
            except UnicodeEncodeError:
                return ''.join(c if ord(c) < 128 else '?' for c in n)
        print(f"\n  EN IYI  : {safe_sym(best['symbol'])} {best['direction']} ${best['dollar_pnl']:+.2f}")
        print(f"  EN KOTU : {safe_sym(worst['symbol'])} {worst['direction']} ${worst['dollar_pnl']:+.2f}")
    else:
        print("  [X] Hic islem bulunamadi!")
    
    print("\n" + hdr)
    return executed_trades, backtest_coin.signals if hasattr(backtest_coin, 'signals') else []


if __name__ == "__main__":
    trades, signals = run_backtest()
