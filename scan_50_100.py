import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import warnings
import time
import sys
from datetime import datetime

warnings.filterwarnings('ignore')
pd.set_option('future.no_silent_downcasting', True)

# ==========================================
# ⚙️ AYARLAR
# ==========================================
TELEGRAM_TOKEN = '8063148867:AAH2UX__oKRPtXGyZWtBEmMJOZOMY1GN3Lc'
CHAT_ID = '6786568689'
TIMEFRAMES = ['1d', '1h', '15m']
TF_NAMES = {'1d': 'Günlük', '1h': 'Saatlik', '15m': '15dk'}
TF_RELIABILITY = {'1d': 10, '1h': 5, '15m': -5}

# Tarama aralığı: 1-100 arası
START_RANK = 1
END_RANK = 100
SCORE_THRESHOLD = 50
MIN_WIN_RATE = 60
TOP_SIGNALS = 3  # En iyi 3 coin

# ==========================================
# 🔌 BORSA BAĞLANTISI
# ==========================================
exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except: pass

def get_whale_ratio(symbol):
    try:
        clean = symbol.replace('/', '').split(':')[0]
        r = requests.get(f"https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={clean}&period=1h&limit=1", timeout=5).json()
        return float(r[0]['longShortRatio']) if r else 1.0
    except: return 1.0

def get_global_ls(symbol):
    try:
        clean = symbol.replace('/', '').split(':')[0]
        r = requests.get(f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={clean}&period=1h&limit=1", timeout=5).json()
        return float(r[0]['longShortRatio']) if r else 1.0
    except: return 1.0

def get_funding(symbol):
    try:
        clean = symbol.replace('/', '').split(':')[0]
        r = requests.get(f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={clean}&limit=1", timeout=5).json()
        return float(r[0]['fundingRate']) if r else 0.0
    except: return 0.0

def fetch_ohlcv(symbol, tf):
    for _ in range(3):
        try:
            data = exchange.fetch_ohlcv(symbol, tf, limit=150)
            if data and len(data) >= 50:
                return data
        except:
            time.sleep(0.5)
    return None

def analyze_tf(symbol, tf):
    """Tek timeframe SHORT analizi"""
    ohlcv = fetch_ohlcv(symbol, tf)
    if not ohlcv:
        return None
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # İndikatörler
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    df['sma50'] = ta.sma(df['close'], length=50)
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
        df['bb_middle'] = bb.iloc[:, 1]
        df['bb_upper'] = bb.iloc[:, 2]
        df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    else:
        df['bb_pct'] = 0.5
    
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
    
    df = df.ffill().fillna(0).infer_objects(copy=False)
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last['close'])
    
    # SHORT puanlama
    score = 0
    reasons = []
    
    # ADX + DI
    adx = float(last['adx']) if pd.notna(last['adx']) else 0
    di_plus = float(last['di_plus']) if pd.notna(last['di_plus']) else 0
    di_minus = float(last['di_minus']) if pd.notna(last['di_minus']) else 0
    
    if adx > 25 and di_minus > di_plus:
        score += 30
        reasons.append(f"ADX Güçlü ({adx:.0f}) + DI-")
    elif di_minus > di_plus:
        score += 15
        reasons.append("DI- > DI+")
    
    # EMA
    ema9 = float(last['ema9']) if pd.notna(last['ema9']) else price
    ema21 = float(last['ema21']) if pd.notna(last['ema21']) else price
    sma50 = float(last['sma50']) if pd.notna(last['sma50']) else price
    
    if ema9 < ema21 < sma50:
        score += 25
        reasons.append("EMA Bearish")
    elif ema9 < ema21:
        score += 15
        reasons.append("EMA9 < EMA21")
    
    # RSI
    rsi = float(last['rsi']) if pd.notna(last['rsi']) else 50
    if rsi > 70:
        score += 25
        reasons.append(f"RSI Aşırı Alım ({rsi:.0f})")
    elif rsi > 60:
        score += 15
        reasons.append(f"RSI Yüksek ({rsi:.0f})")
    
    # MACD
    macd_val = float(last['macd']) if pd.notna(last['macd']) else 0
    macd_sig = float(last['macd_signal']) if pd.notna(last['macd_signal']) else 0
    
    if macd_val < macd_sig:
        score += 20
        reasons.append("MACD Bearish")
    
    # Bollinger
    bb_pct = float(last['bb_pct']) if pd.notna(last['bb_pct']) else 0.5
    if bb_pct > 0.95:
        score += 25
        reasons.append(f"BB Üst ({bb_pct*100:.0f}%)")
    elif bb_pct > 0.8:
        score += 15
        reasons.append(f"BB Yüksek ({bb_pct*100:.0f}%)")
    
    # StochRSI
    stoch_k = float(last['stoch_k']) if pd.notna(last['stoch_k']) else 50
    if stoch_k > 80:
        score += 20
        reasons.append(f"StochRSI ({stoch_k:.0f})")
    
    # MFI
    mfi = float(last['mfi']) if pd.notna(last['mfi']) else 50
    if mfi > 80:
        score += 15
        reasons.append(f"MFI ({mfi:.0f})")
    
    atr = float(last['atr']) if pd.notna(last['atr']) else price * 0.02
    
    return {
        'tf': tf,
        'score': score,
        'price': price,
        'atr': atr,
        'rsi': rsi,
        'adx': adx,
        'bb_pct': bb_pct,
        'reasons': reasons
    }

def calculate_win_rate(tf_results):
    """Win rate hesapla"""
    win_rates = {}
    short_tfs = []
    
    for tf, result in tf_results.items():
        if result and result['score'] >= SCORE_THRESHOLD:
            short_tfs.append(tf)
            wr = 50
            if result['score'] >= 80: wr += 15
            elif result['score'] >= 60: wr += 10
            elif result['score'] >= 50: wr += 5
            wr += TF_RELIABILITY.get(tf, 0)
            win_rates[tf] = wr
    
    if len(short_tfs) >= 3:
        for tf in win_rates: win_rates[tf] += 10
    elif len(short_tfs) >= 2:
        for tf in win_rates: win_rates[tf] += 5
    
    if '1d' in short_tfs and '1h' in short_tfs:
        if '1h' in win_rates: win_rates['1h'] += 10
    
    return win_rates, short_tfs

def select_best_tf(tf_results, win_rates, short_tfs):
    if not short_tfs:
        return None, 0
    if len(short_tfs) == 3:
        return '1h', win_rates.get('1h', 0)
    if '1d' in short_tfs and '1h' in short_tfs:
        return '1h', win_rates.get('1h', 0)
    best_tf = max(win_rates, key=win_rates.get)
    return best_tf, win_rates[best_tf]

def analyze_coin(symbol, rank):
    """Multi-TF analiz"""
    tf_results = {}
    for tf in TIMEFRAMES:
        result = analyze_tf(symbol, tf)
        tf_results[tf] = result
        time.sleep(0.15)
    
    win_rates, short_tfs = calculate_win_rate(tf_results)
    
    if not short_tfs:
        return None
    
    best_tf, win_rate = select_best_tf(tf_results, win_rates, short_tfs)
    
    if win_rate < MIN_WIN_RATE:
        return None
    
    selected = tf_results[best_tf]
    if not selected:
        return None
    
    # Binance data
    whale = get_whale_ratio(symbol)
    global_ls = get_global_ls(symbol)
    funding = get_funding(symbol)
    
    # Bonus
    if whale < 0.9: win_rate += 3
    if global_ls > 1.5: win_rate += 3
    if funding > 0.0005: win_rate += 2
    
    price = selected['price']
    atr = selected['atr']
    stop = price + (atr * 1.5)
    risk = abs(price - stop)
    tp1 = price - (risk * 1.5)
    tp2 = price - (risk * 2.5)
    tp3 = price - (risk * 4)
    
    # TF skorları
    tf_scores = {}
    for tf, res in tf_results.items():
        if res:
            tf_scores[tf] = res['score']
    
    return {
        'symbol': symbol,
        'rank': rank,
        'best_tf': best_tf,
        'win_rate': min(win_rate, 95),
        'score': selected['score'],
        'price': price,
        'stop': stop,
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3,
        'tf_scores': tf_scores,
        'short_tfs': short_tfs,
        'reasons': selected['reasons'],
        'rsi': selected['rsi'],
        'adx': selected['adx'],
        'whale': whale,
        'global_ls': global_ls,
        'funding': funding
    }

def get_symbols_by_volume():
    """Hacme göre sırala"""
    tickers = exchange.fetch_tickers()
    pairs = []
    for s, d in tickers.items():
        if '/USDT' in s:
            vol = float(d.get('quoteVolume', 0) or 0)
            if vol > 0:
                pairs.append({'symbol': s, 'volume': vol})
    pairs.sort(key=lambda x: x['volume'], reverse=True)
    return pairs

# ==========================================
# 🚀 ANA
# ==========================================
print("="*70)
print(f"🔍 HACIM SIRASI {START_RANK}-{END_RANK} ARASI COİN ANALİZİ")
print("="*70)

# Coinleri al
all_pairs = get_symbols_by_volume()
target_pairs = all_pairs[START_RANK-1:END_RANK]  # 50-100 arası

print(f"\n📊 Toplam {len(target_pairs)} coin analiz edilecek (Sıra {START_RANK}-{END_RANK})")
print("-"*70)

# Analiz
signals = []

for i, p in enumerate(target_pairs):
    symbol = p['symbol']
    rank = START_RANK + i
    volume = p['volume']
    
    print(f"\n[{rank}] {symbol} (Hacim: ${volume/1e6:.1f}M)")
    
    result = analyze_coin(symbol, rank)
    
    if result:
        print(f"   ✅ SHORT SİNYALİ | WR: {result['win_rate']:.0f}% | Puan: {result['score']}")
        print(f"   📊 TF Skorları: 1D={result['tf_scores'].get('1d', 0)} | 1H={result['tf_scores'].get('1h', 0)} | 15M={result['tf_scores'].get('15m', 0)}")
        print(f"   📈 RSI: {result['rsi']:.0f} | ADX: {result['adx']:.0f}")
        print(f"   🐋 Whale: {result['whale']:.2f} | Global L/S: {result['global_ls']:.2f}")
        print(f"   💡 Sebepler: {', '.join(result['reasons'][:4])}")
        signals.append(result)
    else:
        print(f"   ❌ Short sinyali yok")
    
    time.sleep(0.3)

# Sıralama
signals.sort(key=lambda x: (x['win_rate'], x['score']), reverse=True)

print("\n" + "="*70)
print(f"📊 SONUÇ: {len(signals)} coin SHORT sinyali verdi")
print("="*70)

# En iyi 3
top = signals[:TOP_SIGNALS]

if top:
    print(f"\n🏆 EN İYİ {TOP_SIGNALS} SHORT SİNYALİ:")
    print("-"*70)
    
    for i, s in enumerate(top):
        risk_pct = abs(s['price'] - s['stop']) / s['price'] * 100
        
        print(f"""
{i+1}. {s['symbol'].split('/')[0]} (Sıra #{s['rank']})
   Win Rate: {s['win_rate']:.0f}% | Puan: {s['score']}
   Seçilen TF: {TF_NAMES[s['best_tf']]}
   Fiyat: ${s['price']:.4f}
   Stop: ${s['stop']:.4f} ({risk_pct:.1f}%)
   TP1: ${s['tp1']:.4f} | TP2: ${s['tp2']:.4f} | TP3: ${s['tp3']:.4f}
   RSI: {s['rsi']:.0f} | ADX: {s['adx']:.0f}
   Whale: {s['whale']:.2f} | Global L/S: {s['global_ls']:.2f}
   Sebepler: {', '.join(s['reasons'])}
""")
        
        # Telegram gönder
        tf_info = f"1D={s['tf_scores'].get('1d', 0)} | 1H={s['tf_scores'].get('1h', 0)} | 15M={s['tf_scores'].get('15m', 0)}"
        reasons_text = "\n".join([f"  • {r}" for r in s['reasons']])
        
        msg = f"""🔻 <b>#{s['symbol'].split('/')[0]} - SHORT (5x)</b>
━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>Win Rate: {s['win_rate']:.0f}%</b>
⏱ <b>Seçilen TF:</b> {TF_NAMES[s['best_tf']]}
⭐ <b>Puan:</b> {s['score']}/200
🏆 <b>Hacim Sırası:</b> #{s['rank']} ({START_RANK}-{END_RANK} arası)
━━━━━━━━━━━━━━━━━━━━━━
📊 <b>TF Skorları:</b> {tf_info}
━━━━━━━━━━━━━━━━━━━━━━
📥 <b>GİRİŞ:</b> ${s['price']:.4f}
🛑 <b>STOP:</b> ${s['stop']:.4f} ({risk_pct:.1f}%)
━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>TP1:</b> ${s['tp1']:.4f} (1:1.5)
🎯 <b>TP2:</b> ${s['tp2']:.4f} (1:2.5)
🎯 <b>TP3:</b> ${s['tp3']:.4f} (1:4)
━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Veriler:</b>
  🐋 Whale: {s['whale']:.2f} | 📈 G.L/S: {s['global_ls']:.2f}
  📊 RSI: {s['rsi']:.0f} | ADX: {s['adx']:.0f}
━━━━━━━━━━━━━━━━━━━━━━
<b>Sebepler:</b>
{reasons_text}
━━━━━━━━━━━━━━━━━━━━━━
⚠️ <i>DYOR - Finansal tavsiye değildir</i>"""
        
        send_telegram(msg)
        print(f"   📤 Telegram'a gönderildi!")
        time.sleep(1)

else:
    print("\n❌ Short sinyali bulunamadı!")
    send_telegram(f"❌ {START_RANK}-{END_RANK} arası coinlerde SHORT sinyali bulunamadı.")

print("\n" + "="*70)
print("✅ ANALİZ TAMAMLANDI")
print("="*70)
