import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import time
import sys
import warnings
from datetime import datetime

# Pandas uyarılarını kapat
warnings.filterwarnings('ignore', category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

# ==========================================
# ⚙️ ULTRA SHORT BOT - MULTI TIMEFRAME
# ==========================================
API_KEY = 'YOUR_API_KEY_HERE'
SECRET_KEY = 'YOUR_SECRET_KEY_HERE'
TELEGRAM_TOKEN = '8063148867:AAH2UX__oKRPtXGyZWtBEmMJOZOMY1GN3Lc'
CHAT_ID = '6786568689'

# Multi-Timeframe Ayarları
TIMEFRAMES = ['1d', '1h', '15m']
TF_NAMES = {'1d': 'Günlük', '1h': 'Saatlik', '15m': '15 Dakika'}
TF_RELIABILITY = {'1d': 10, '1h': 5, '15m': -5}  # Win rate bonus

# Strateji Ayarları
LEVERAGE_MSG = "5x"
SCORE_THRESHOLD = 50           # TF bazında min puan
STRONG_SIGNAL_THRESHOLD = 70   # Güçlü sinyal eşiği
MAX_SIGNALS_PER_HOUR = 10
MIN_VOLUME_USD = 40_000_000    # 40M USD
SCAN_COIN_COUNT = 80
MIN_WIN_RATE = 60              # Minimum %60 Win Rate

# ==========================================
# 🔌 BORSA BAĞLANTISI
# ==========================================
try:
    exchange_config = {
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    }
    
    if API_KEY != 'YOUR_API_KEY_HERE':
        exchange_config['apiKey'] = API_KEY
        exchange_config['secret'] = SECRET_KEY
    else:
        print("ℹ️ API Anahtarı girilmedi. Bot 'Public Mod'da çalışacak.")

    exchange = ccxt.binance(exchange_config)
except Exception as e:
    print(f"Bağlantı Hatası: {e}")
    sys.exit()

# ==========================================
# 🛠️ YARDIMCI FONKSİYONLAR
# ==========================================

def send_telegram_message(message):
    """Telegram üzerinden mesaj gönderir."""
    if TELEGRAM_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN':
        print(f"TELEGRAM: {message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def get_funding_rate(symbol):
    """Binance Futures Funding Rate."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={clean_symbol}&limit=1"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list) and len(response) > 0:
            return float(response[0]['fundingRate'])
        return 0.0
    except:
        return 0.0

def get_open_interest_change(symbol):
    """Open Interest değişimi (son 4 saat)."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={clean_symbol}&period=1h&limit=4"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list) and len(response) >= 2:
            current = float(response[-1]['sumOpenInterest'])
            prev = float(response[0]['sumOpenInterest'])
            if prev > 0:
                return ((current - prev) / prev) * 100
        return 0.0
    except:
        return 0.0

def get_taker_ratio(symbol):
    """Taker Buy/Sell Ratio."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/futures/data/takerlongshortRatio?symbol={clean_symbol}&period=1h&limit=1"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list) and len(response) > 0:
            return float(response[0]['buySellRatio'])
        return 1.0
    except:
        return 1.0

def get_whale_ratio(symbol):
    """Top Trader Long/Short Ratio."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={clean_symbol}&period=1h&limit=1"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list):
            return float(response[0]['longShortRatio'])
        return 1.0
    except:
        return 1.0

def get_global_ls_ratio(symbol):
    """Global Long/Short Ratio."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={clean_symbol}&period=1h&limit=1"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list):
            return float(response[0]['longShortRatio'])
        return 1.0
    except:
        return 1.0

def fetch_ohlcv_safe(symbol, timeframe, limit=150):
    """Güvenli OHLCV veri çekme."""
    for attempt in range(3):
        try:
            data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if data and len(data) >= 50:
                return data
        except:
            if attempt < 2:
                time.sleep(1)
    return None

def calculate_risk_reward(entry, stop):
    """SHORT için TP seviyeleri."""
    risk = abs(entry - stop)
    tp1 = entry - (risk * 1.5)   # 1:1.5 R:R
    tp2 = entry - (risk * 2.5)   # 1:2.5 R:R
    tp3 = entry - (risk * 4)     # 1:4 R:R
    return tp1, tp2, tp3

# ==========================================
# 🧠 TEK TIMEFRAME ANALİZ MOTORU
# ==========================================

def analyze_timeframe(symbol, timeframe):
    """
    Tek timeframe için SHORT analizi.
    İndikatörler: BB, ADX, MACD, MA, RSI, Stoch, MFI, OBV, CCI
    Maksimum Puan: 200
    """
    try:
        ohlcv = fetch_ohlcv_safe(symbol, timeframe)
        if not ohlcv:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # ═══════════════════════════════════════════════════════════════
        # KAPSAMLI İNDİKATÖR HESAPLAMALARI
        # ═══════════════════════════════════════════════════════════════
        
        # Moving Averages
        df['ema9'] = ta.ema(df['close'], length=9)
        df['ema21'] = ta.ema(df['close'], length=21)
        df['sma50'] = ta.sma(df['close'], length=50)
        df['sma100'] = ta.sma(df['close'], length=100)
        df['sma200'] = ta.sma(df['close'], length=200)
        
        # RSI
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # MACD
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['macd'] = macd.iloc[:, 0]
            df['macd_signal'] = macd.iloc[:, 1]
            df['macd_hist'] = macd.iloc[:, 2]
        else:
            df['macd'] = df['macd_signal'] = df['macd_hist'] = 0
        
        # Bollinger Bands
        bb = ta.bbands(df['close'], length=20, std=2)
        if bb is not None:
            df['bb_lower'] = bb.iloc[:, 0]
            df['bb_middle'] = bb.iloc[:, 1]
            df['bb_upper'] = bb.iloc[:, 2]
            df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        else:
            df['bb_lower'] = df['close'] * 0.98
            df['bb_middle'] = df['close']
            df['bb_upper'] = df['close'] * 1.02
            df['bb_pct'] = 0.5
        
        # ADX + DI
        adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx_data is not None:
            df['adx'] = adx_data.iloc[:, 0]
            df['di_plus'] = adx_data.iloc[:, 1]
            df['di_minus'] = adx_data.iloc[:, 2]
        else:
            df['adx'] = df['di_plus'] = df['di_minus'] = 0
        
        # Stochastic RSI
        stoch_rsi = ta.stochrsi(df['close'], length=14)
        if stoch_rsi is not None:
            df['stoch_k'] = stoch_rsi.iloc[:, 0]
            df['stoch_d'] = stoch_rsi.iloc[:, 1]
        else:
            df['stoch_k'] = df['stoch_d'] = 50
        
        # MFI (Money Flow Index)
        df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)
        
        # OBV (On Balance Volume)
        df['obv'] = ta.obv(df['close'], df['volume'])
        df['obv_ema'] = ta.ema(df['obv'], length=20)
        
        # CCI (Commodity Channel Index)
        df['cci'] = ta.cci(df['high'], df['low'], df['close'], length=20)
        
        # ATR
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Volume
        df['vol_sma'] = ta.sma(df['volume'], length=20)
        
        # NaN temizle
        df = df.ffill()
        df = df.fillna(0)
        df = df.infer_objects(copy=False)
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        price = float(last['close'])
        
        # ═══════════════════════════════════════════════════════════════
        # SHORT PUANLAMA SİSTEMİ (Maks 200 puan)
        # ═══════════════════════════════════════════════════════════════
        score = 0
        reasons = []
        
        # --- 1. ADX + DI (Trend Gücü) - Maks: 30p ---
        adx = float(last['adx']) if pd.notna(last['adx']) else 0
        di_plus = float(last['di_plus']) if pd.notna(last['di_plus']) else 0
        di_minus = float(last['di_minus']) if pd.notna(last['di_minus']) else 0
        
        if adx > 30 and di_minus > di_plus:
            score += 30
            reasons.append(f"🔥 ADX Çok Güçlü ({adx:.0f}) + DI-: +30p")
        elif adx > 25 and di_minus > di_plus:
            score += 25
            reasons.append(f"📉 ADX Güçlü ({adx:.0f}) + DI-: +25p")
        elif adx > 20 and di_minus > di_plus:
            score += 18
            reasons.append(f"📊 ADX Orta ({adx:.0f}) + DI-: +18p")
        elif di_minus > di_plus * 1.15:
            score += 12
            reasons.append(f"📉 DI- > DI+ ({di_minus:.0f}>{di_plus:.0f}): +12p")
        
        # --- 2. EMA/SMA Dizilimi - Maks: 30p ---
        ema9 = float(last['ema9']) if pd.notna(last['ema9']) else price
        ema21 = float(last['ema21']) if pd.notna(last['ema21']) else price
        sma50 = float(last['sma50']) if pd.notna(last['sma50']) else price
        sma100 = float(last['sma100']) if pd.notna(last['sma100']) else price
        sma200 = float(last['sma200']) if pd.notna(last['sma200']) else price
        
        # Death Cross kontrolü (EMA9 < EMA21)
        prev_ema9 = float(prev['ema9']) if pd.notna(prev['ema9']) else price
        prev_ema21 = float(prev['ema21']) if pd.notna(prev['ema21']) else price
        
        if price < ema9 < ema21 < sma50 < sma100:
            score += 30
            reasons.append("🔴 Mükemmel Bearish Dizilim: +30p")
        elif ema9 < ema21 < sma50:
            score += 22
            reasons.append("📉 Bearish EMA/SMA: +22p")
        elif ema9 < ema21 and price < sma50:
            score += 16
            reasons.append("📊 EMA Bearish + Fiyat<SMA50: +16p")
        elif prev_ema9 >= prev_ema21 and ema9 < ema21:  # Death Cross oluştu
            score += 25
            reasons.append("💀 DEATH CROSS (EMA9<EMA21): +25p")
        elif price < ema21:
            score += 10
            reasons.append("📊 Fiyat < EMA21: +10p")
        
        # SMA200 altında = bearish trend
        if price < sma200:
            score += 8
            reasons.append("📉 Fiyat < SMA200 (Bearish Trend): +8p")
        
        # --- 3. RSI - Maks: 30p ---
        rsi = float(last['rsi']) if pd.notna(last['rsi']) else 50
        
        if rsi > 80:
            score += 30
            reasons.append(f"🔥 RSI Aşırı Alım ({rsi:.0f}): +30p")
        elif rsi > 70:
            score += 25
            reasons.append(f"📈 RSI Yüksek ({rsi:.0f}): +25p")
        elif rsi > 60:
            score += 15
            reasons.append(f"📊 RSI Orta-Yüksek ({rsi:.0f}): +15p")
        elif rsi > 50 and rsi < 60:
            score += 8
            reasons.append(f"📊 RSI Nötr-Yüksek ({rsi:.0f}): +8p")
        
        # RSI Divergence (basit kontrol)
        prev_rsi = float(prev['rsi']) if pd.notna(prev['rsi']) else 50
        if price > float(prev['close']) and rsi < prev_rsi and rsi > 60:
            score += 10
            reasons.append("⚠️ RSI Bearish Divergence: +10p")
        
        # --- 4. MACD - Maks: 30p ---
        macd_val = float(last['macd']) if pd.notna(last['macd']) else 0
        macd_sig = float(last['macd_signal']) if pd.notna(last['macd_signal']) else 0
        macd_hist = float(last['macd_hist']) if pd.notna(last['macd_hist']) else 0
        prev_macd_hist = float(prev['macd_hist']) if pd.notna(prev['macd_hist']) else 0
        prev_macd = float(prev['macd']) if pd.notna(prev['macd']) else 0
        prev_macd_sig = float(prev['macd_signal']) if pd.notna(prev['macd_signal']) else 0
        
        # MACD Bearish Cross (yeni oluştu)
        if prev_macd >= prev_macd_sig and macd_val < macd_sig:
            score += 30
            reasons.append("💀 MACD Bearish Cross (YENİ): +30p")
        elif macd_val < macd_sig and macd_hist < 0:
            score += 22
            reasons.append("📉 MACD < Signal + Negatif Hist: +22p")
        elif macd_val < macd_sig:
            score += 15
            reasons.append("📉 MACD < Signal: +15p")
        elif macd_hist < prev_macd_hist and macd_hist < 0:
            score += 10
            reasons.append("📊 MACD Hist Düşüyor: +10p")
        
        # --- 5. Bollinger Bands - Maks: 30p ---
        bb_upper = float(last['bb_upper']) if pd.notna(last['bb_upper']) else price * 1.02
        bb_middle = float(last['bb_middle']) if pd.notna(last['bb_middle']) else price
        bb_lower = float(last['bb_lower']) if pd.notna(last['bb_lower']) else price * 0.98
        bb_pct = float(last['bb_pct']) if pd.notna(last['bb_pct']) else 0.5
        
        if price >= bb_upper:
            score += 30
            reasons.append("🔴 BB ÜST BANT AŞIMI: +30p")
        elif bb_pct > 0.95:
            score += 25
            reasons.append(f"📈 BB Üst Bant Teması ({bb_pct*100:.0f}%): +25p")
        elif bb_pct > 0.85:
            score += 18
            reasons.append(f"📊 BB Üst Bölge ({bb_pct*100:.0f}%): +18p")
        elif bb_pct > 0.7 and price > bb_middle:
            score += 10
            reasons.append(f"📊 BB Orta-Üst ({bb_pct*100:.0f}%): +10p")
        
        # --- 6. Stochastic RSI - Maks: 20p ---
        stoch_k = float(last['stoch_k']) if pd.notna(last['stoch_k']) else 50
        stoch_d = float(last['stoch_d']) if pd.notna(last['stoch_d']) else 50
        
        if stoch_k > 90:
            score += 20
            reasons.append(f"🔥 StochRSI Extrem ({stoch_k:.0f}): +20p")
        elif stoch_k > 80:
            score += 15
            reasons.append(f"📈 StochRSI Aşırı Alım ({stoch_k:.0f}): +15p")
        elif stoch_k > 70 and stoch_k < stoch_d:  # Bearish cross
            score += 12
            reasons.append(f"📉 StochRSI Bearish ({stoch_k:.0f}): +12p")
        
        # --- 7. MFI (Money Flow Index) - Maks: 15p ---
        mfi = float(last['mfi']) if pd.notna(last['mfi']) else 50
        
        if mfi > 85:
            score += 15
            reasons.append(f"💰 MFI Aşırı Alım ({mfi:.0f}): +15p")
        elif mfi > 75:
            score += 10
            reasons.append(f"💰 MFI Yüksek ({mfi:.0f}): +10p")
        
        # --- 8. OBV Trend - Maks: 15p ---
        obv = float(last['obv']) if pd.notna(last['obv']) else 0
        obv_ema = float(last['obv_ema']) if pd.notna(last['obv_ema']) else obv
        
        if obv < obv_ema:
            score += 15
            reasons.append("📉 OBV < OBV_EMA (Satış Baskısı): +15p")
        
        # --- 9. CCI - Maks: 15p ---
        cci = float(last['cci']) if pd.notna(last['cci']) else 0
        
        if cci > 150:
            score += 15
            reasons.append(f"🔥 CCI Extrem ({cci:.0f}): +15p")
        elif cci > 100:
            score += 10
            reasons.append(f"📈 CCI Yüksek ({cci:.0f}): +10p")
        
        # --- 10. Volume Analizi - Maks: 10p ---
        vol = float(last['volume']) if pd.notna(last['volume']) else 0
        vol_sma = float(last['vol_sma']) if pd.notna(last['vol_sma']) else vol
        
        is_red_candle = last['close'] < last['open']
        if vol > vol_sma * 1.5 and is_red_candle:
            score += 10
            reasons.append("📊 Yüksek Hacim + Kırmızı Mum: +10p")
        
        # ATR hesapla
        atr = float(last['atr']) if pd.notna(last['atr']) else price * 0.02
        
        return {
            'tf': timeframe,
            'score': score,
            'price': price,
            'atr': atr,
            'adx': adx,
            'rsi': rsi,
            'macd_hist': macd_hist,
            'bb_pct': bb_pct,
            'bb_upper': bb_upper,
            'reasons': reasons
        }

    except Exception as e:
        return None

# ==========================================
# 🎯 WIN RATE HESAPLAMA
# ==========================================

def calculate_win_rate(tf_results):
    """
    Multi-timeframe sonuçlarına göre Win Rate hesaplar.
    """
    win_rates = {}
    short_tfs = []
    
    for tf, result in tf_results.items():
        if result and result['score'] >= SCORE_THRESHOLD:
            short_tfs.append(tf)
            
            # Baz oran: %50
            wr = 50
            
            # Puan bonusu (0-15%)
            if result['score'] >= 80:
                wr += 15
            elif result['score'] >= 65:
                wr += 10
            elif result['score'] >= 50:
                wr += 5
            
            # Timeframe güvenilirlik bonusu
            wr += TF_RELIABILITY.get(tf, 0)
            
            win_rates[tf] = wr
    
    # Confluence bonusu (çoklu TF uyumu)
    if len(short_tfs) >= 3:  # Tüm TF'ler SHORT
        for tf in win_rates:
            win_rates[tf] += 10
    elif len(short_tfs) >= 2:  # 2 TF SHORT
        for tf in win_rates:
            win_rates[tf] += 5
    
    # Trend uyumu bonusu (Günlük ile saatlik aynı yönde)
    if '1d' in short_tfs and '1h' in short_tfs:
        if '1h' in win_rates:
            win_rates['1h'] += 10
        if '15m' in win_rates:
            win_rates['15m'] += 8
    
    return win_rates, short_tfs

def select_best_timeframe(tf_results, win_rates, short_tfs):
    """
    En iyi timeframe'i seçer.
    """
    if not short_tfs:
        return None, 0
    
    # Tüm TF'ler SHORT ise 1H tercih et (dengeli)
    if len(short_tfs) == 3:
        return '1h', win_rates.get('1h', 0)
    
    # 1D + 1H SHORT ise 1H kullan
    if '1d' in short_tfs and '1h' in short_tfs:
        return '1h', win_rates.get('1h', 0)
    
    # 1H + 15M SHORT ise, skor yüksek olanı seç
    if '1h' in short_tfs and '15m' in short_tfs:
        if tf_results['15m']['score'] > tf_results['1h']['score'] + 15:
            return '15m', win_rates.get('15m', 0)
        return '1h', win_rates.get('1h', 0)
    
    # En yüksek Win Rate olanı seç
    best_tf = max(win_rates, key=win_rates.get)
    return best_tf, win_rates[best_tf]

# ==========================================
# 🔥 ANA ANALİZ FONKSİYONU
# ==========================================

def analyze_multi_timeframe(symbol, rank):
    """
    3 timeframe analiz eder ve en iyi SHORT fırsatını seçer.
    """
    try:
        # Tüm timeframe'leri analiz et
        tf_results = {}
        for tf in TIMEFRAMES:
            result = analyze_timeframe(symbol, tf)
            tf_results[tf] = result
            time.sleep(0.2)  # Rate limit
        
        # Win rate hesapla
        win_rates, short_tfs = calculate_win_rate(tf_results)
        
        # Hiç SHORT sinyal yoksa atla
        if not short_tfs:
            return None
        
        # En iyi TF'i seç
        best_tf, win_rate = select_best_timeframe(tf_results, win_rates, short_tfs)
        
        # Minimum win rate kontrolü
        if win_rate < MIN_WIN_RATE:
            return None
        
        # Seçilen TF'in detaylarını al
        selected = tf_results[best_tf]
        if not selected:
            return None
        
        # Binance verileri
        whale = get_whale_ratio(symbol)
        global_ls = get_global_ls_ratio(symbol)
        funding = get_funding_rate(symbol)
        oi_change = get_open_interest_change(symbol)
        taker = get_taker_ratio(symbol)
        
        # Binance data bonusu
        binance_bonus = 0
        binance_reasons = []
        
        if whale < 0.9:
            binance_bonus += 5
            binance_reasons.append(f"🐋 Balinalar SHORT ({whale:.2f})")
            win_rate += 3
        
        if global_ls > 1.5:  # Herkes LONG = Short fırsatı
            binance_bonus += 5
            binance_reasons.append(f"⚠️ Kalabalık LONG ({global_ls:.2f})")
            win_rate += 3
        
        if funding > 0.0005:
            binance_bonus += 3
            binance_reasons.append(f"💰 Pozitif Funding ({funding*100:.3f}%)")
            win_rate += 2
        
        if taker < 0.9:
            binance_bonus += 3
            binance_reasons.append(f"📉 Taker Satış ({taker:.2f})")
            win_rate += 2
        
        # Final skor
        final_score = selected['score'] + binance_bonus
        
        # Stop Loss ve TP hesapla
        price = selected['price']
        atr = selected['atr']
        stop_loss = price + (atr * 1.5)
        tp1, tp2, tp3 = calculate_risk_reward(price, stop_loss)
        
        return {
            'symbol': symbol,
            'rank': rank,
            'best_tf': best_tf,
            'win_rate': min(win_rate, 95),  # Max %95
            'score': final_score,
            'price': price,
            'stop': stop_loss,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'tf_results': tf_results,
            'short_tfs': short_tfs,
            'win_rates': win_rates,
            'reasons': selected['reasons'] + binance_reasons,
            'adx': selected['adx'],
            'rsi': selected['rsi'],
            'bb_upper': selected['bb_upper'],
            'whale': whale,
            'global_ls': global_ls,
            'funding': funding,
            'oi_change': oi_change,
            'taker': taker
        }
        
    except Exception as e:
        print(f"      ❌ HATA ({symbol}): {str(e)}")
        return None

# ==========================================
# 🚀 ANA DÖNGÜ
# ==========================================

def get_symbols_by_volume():
    """Futures çiftlerini hacme göre sıralar."""
    try:
        tickers = exchange.fetch_tickers()
        pairs = []
        for s, d in tickers.items():
            if '/USDT' in s:
                vol = float(d.get('quoteVolume', 0) or 0)
                if vol >= MIN_VOLUME_USD:
                    pairs.append({'symbol': s, 'volume': vol})
        
        pairs.sort(key=lambda x: x['volume'], reverse=True)
        print(f"   📊 {len(pairs)} Futures çifti (>{MIN_VOLUME_USD/1e6:.0f}M$)")
        return [p['symbol'] for p in pairs]
    except Exception as e:
        print(f"Ticker Hatası: {e}")
        return []

def main():
    print("="*60)
    print("🔻 ULTRA SHORT BOT - MULTI TIMEFRAME")
    print("="*60)
    print(f"⏱ Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"💰 Min Hacim: {MIN_VOLUME_USD/1e6:.0f}M$")
    print(f"🎯 Min Win Rate: {MIN_WIN_RATE}%")
    print(f"📊 İndikatörler: BB, ADX, MACD, MA, RSI, StochRSI, MFI, OBV, CCI")
    print("="*60)
    
    send_telegram_message(
        f"🔻 <b>ULTRA SHORT BOT Başlatıldı!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ Timeframes: 1D, 1H, 15M\n"
        f"💰 Min Hacim: {MIN_VOLUME_USD/1e6:.0f}M$\n"
        f"🎯 Multi-TF Analiz + Win Rate\n"
        f"📊 9 İndikatör + Binance Data"
    )

    while True:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Tarama Başlıyor...")
            all_symbols = get_symbols_by_volume()
            
            signals = []
            scan_count = min(SCAN_COIN_COUNT, len(all_symbols))
            
            print(f"   🔍 {scan_count} coin taranıyor (3 TF)...")

            for i, symbol in enumerate(all_symbols[:scan_count]):
                result = analyze_multi_timeframe(symbol, i+1)
                
                if result:
                    print(f"   ✅ {symbol:<12} | TF: {result['best_tf']} | WR: {result['win_rate']:.0f}% | Puan: {result['score']}")
                    signals.append(result)
                    
                if len(signals) >= MAX_SIGNALS_PER_HOUR:
                    break
                
                if (i + 1) % 5 == 0:
                    time.sleep(0.5)
            
            print(f"   📊 {len(signals)} sinyal bulundu")
            
            # Win Rate'e göre sırala
            signals.sort(key=lambda x: (x['win_rate'], x['score']), reverse=True)
            top_signals = signals[:MAX_SIGNALS_PER_HOUR]
            
            if top_signals:
                for s in top_signals:
                    strength = "💪 GÜÇLÜ" if s['score'] >= STRONG_SIGNAL_THRESHOLD else "📊 Normal"
                    risk_pct = abs(s['price'] - s['stop']) / s['price'] * 100
                    
                    # TF özeti
                    tf_summary = []
                    for tf in TIMEFRAMES:
                        if s['tf_results'].get(tf):
                            sc = s['tf_results'][tf]['score']
                            wr = s['win_rates'].get(tf, 0)
                            marker = "✅" if tf in s['short_tfs'] else "❌"
                            tf_summary.append(f"{TF_NAMES[tf]}: {sc}p {marker}")
                    
                    reasons_text = "\n".join([f"  • {r}" for r in s['reasons'][:7]])
                    
                    msg = (
                        f"🔻 <b>#{s['symbol'].split('/')[0]} - SHORT ({LEVERAGE_MSG})</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 <b>Win Rate: {s['win_rate']:.0f}%</b> ({strength})\n"
                        f"⏱ <b>Seçilen TF:</b> {TF_NAMES[s['best_tf']]}\n"
                        f"⭐ <b>Puan:</b> {s['score']}/200\n"
                        f"🏆 <b>Hacim Sırası:</b> #{s['rank']}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📊 <b>Multi-TF Analiz:</b>\n"
                        f"  {' | '.join(tf_summary)}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📥 <b>GİRİŞ:</b> ${s['price']:.4f}\n"
                        f"🛑 <b>STOP:</b> ${s['stop']:.4f} ({risk_pct:.1f}%)\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 <b>TP1:</b> ${s['tp1']:.4f} (1:1.5)\n"
                        f"🎯 <b>TP2:</b> ${s['tp2']:.4f} (1:2.5)\n"
                        f"🎯 <b>TP3:</b> ${s['tp3']:.4f} (1:4)\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>📊 Binance Data:</b>\n"
                        f"  🐋 Balina: {s['whale']:.2f} | 📈 G.L/S: {s['global_ls']:.2f}\n"
                        f"  💰 Fund: {s['funding']*100:.3f}% | 📊 OI: {s['oi_change']:+.1f}%\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>Sinyal Sebepleri:</b>\n{reasons_text}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚠️ <i>DYOR - Finansal tavsiye değildir</i>"
                    )
                    send_telegram_message(msg)
                    print(f"   📤 Telegram: {s['symbol']} (WR: {s['win_rate']:.0f}%)")
                    time.sleep(1.5)
            else:
                print("   ❌ Uygun sinyal bulunamadı")
            
            print(f"⏳ 3 dakika bekleniyor...")
            time.sleep(180)

        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
