"""
SOL Agresif Test - Günde 5 İşlem, 10x Kaldıraç, Tüm Bakiye
Bu dosya sadece test amaçlıdır, backtest_swing_v2.py'yi ETKİLEMEZ.
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
import warnings
import os
from datetime import datetime, timedelta
from collections import defaultdict

warnings.filterwarnings('ignore')

# ==========================================
# AYARLAR
# ==========================================
DATA_FOLDER = "backtest_data"
INITIAL_BALANCE = 200
LEVERAGE = 10
BACKTEST_START = datetime(2026, 1, 15, 0, 0, 0)
BACKTEST_END = datetime(2026, 2, 10, 23, 59, 59)
MIN_TRADES_PER_DAY = 5
MAX_LOSS_PER_TRADE = -15.0     # Tek islemde max %15 kayip (10x ile %1.5 fiyat hareketi)
SL_ATR_MULT = 1.2              # Siki SL
TP1_RR = 1.0                   # Hizli TP1 (1:1 RR)
TP2_RR = 1.8                   # TP2
TP3_RR = 2.5                   # TP3
TP1_CLOSE = 0.50               # %50 kapat TP1'de
TP2_CLOSE = 0.30               # %30 kapat TP2'de  
TP3_CLOSE = 0.20               # %20 kapat TP3'de


def load_btc():
    df = pd.read_csv(os.path.join(DATA_FOLDER, "BTC_USDT_USDT.csv"))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['rsi'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    if macd is not None:
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 1]
        df['macd_hist'] = macd.iloc[:, 2]
    else:
        df['macd'] = df['macd_signal'] = df['macd_hist'] = 0
    df = df.ffill().fillna(0)
    return df


def get_btc_bias(btc_df, current_time):
    """BTC'nin anlik yonu: 'BULL', 'BEAR', 'NEUTRAL'"""
    mask = btc_df['timestamp'] <= current_time
    if mask.sum() < 30:
        return 'NEUTRAL', 50
    idx = mask.sum() - 1
    row = btc_df.iloc[idx]
    
    p = float(row['close'])
    e9 = float(row['ema9']) if row['ema9'] != 0 else p
    e21 = float(row['ema21']) if row['ema21'] != 0 else p
    e50 = float(row['ema50']) if row['ema50'] != 0 else p
    rsi = float(row['rsi']) if row['rsi'] != 0 else 50
    macd_h = float(row['macd_hist']) if row['macd_hist'] != 0 else 0
    
    bull = 0
    bear = 0
    if p > e9 > e21: bull += 30
    elif p < e9 < e21: bear += 30
    if p > e50: bull += 20
    elif p < e50: bear += 20
    if rsi > 55: bull += 15
    elif rsi < 45: bear += 15
    if macd_h > 0: bull += 15
    elif macd_h < 0: bear += 15
    
    total = bull + bear
    if total == 0: return 'NEUTRAL', 50
    if bull >= bear + 15: return 'BULL', bull
    if bear >= bull + 15: return 'BEAR', bear
    return 'NEUTRAL', max(bull, bear)


def calculate_indicators(df):
    df = df.copy()
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    df['ema50'] = ta.ema(df['close'], length=50)
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
    else:
        df['bb_pct'] = 0.5
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
    
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df['vol_sma'] = ta.sma(df['volume'], length=20)
    df['ema9_slope'] = df['ema9'].diff(5) / df['ema9'].shift(5) * 100
    df['ema21_slope'] = df['ema21'].diff(5) / df['ema21'].shift(5) * 100
    df = df.ffill().fillna(0)
    return df


def score_entry(row, prev_row, btc_bias):
    """
    Akilci giris puanlamasi. Her mumda LONG ve SHORT puani hesapla.
    Returns: (direction, score, confidence)
    """
    price = float(row['close'])
    ema9 = float(row['ema9']) if row['ema9'] != 0 else price
    ema21 = float(row['ema21']) if row['ema21'] != 0 else price
    ema50 = float(row['ema50']) if row['ema50'] != 0 else price
    rsi = float(row['rsi']) if row['rsi'] != 0 else 50
    macd_val = float(row['macd']) if row['macd'] != 0 else 0
    macd_sig = float(row['macd_signal']) if row['macd_signal'] != 0 else 0
    macd_hist = float(row['macd_hist']) if row['macd_hist'] != 0 else 0
    bb_pct = float(row['bb_pct']) if row['bb_pct'] != 0 else 0.5
    adx = float(row['adx']) if row['adx'] != 0 else 0
    di_plus = float(row['di_plus']) if row['di_plus'] != 0 else 0
    di_minus = float(row['di_minus']) if row['di_minus'] != 0 else 0
    stoch_k = float(row['stoch_k']) if row['stoch_k'] != 0 else 50
    ema9_slope = float(row['ema9_slope']) if row['ema9_slope'] != 0 else 0
    vol = float(row['volume']) if row['volume'] != 0 else 0
    vol_sma = float(row['vol_sma']) if row['vol_sma'] != 0 else vol
    
    prev_macd = float(prev_row['macd']) if prev_row['macd'] != 0 else 0
    prev_macd_sig = float(prev_row['macd_signal']) if prev_row['macd_signal'] != 0 else 0
    prev_ema9 = float(prev_row['ema9']) if prev_row['ema9'] != 0 else price
    prev_ema21 = float(prev_row['ema21']) if prev_row['ema21'] != 0 else price
    
    long_s = 0
    short_s = 0
    
    # EMA dizilimi (30p)
    if price > ema9 > ema21:
        long_s += 20
        if ema9_slope > 0: long_s += 10
    if price < ema9 < ema21:
        short_s += 20
        if ema9_slope < 0: short_s += 10
    
    # Golden/Death cross (20p)
    if prev_ema9 <= prev_ema21 and ema9 > ema21: long_s += 20
    if prev_ema9 >= prev_ema21 and ema9 < ema21: short_s += 20
    
    # RSI (15p)
    if rsi < 30: long_s += 15
    elif rsi < 40 and ema9_slope >= 0: long_s += 8
    if rsi > 70: short_s += 15
    elif rsi > 60 and ema9_slope <= 0: short_s += 8
    
    # MACD cross (15p)
    if prev_macd <= prev_macd_sig and macd_val > macd_sig: long_s += 15
    elif macd_val > macd_sig and macd_hist > 0: long_s += 5
    if prev_macd >= prev_macd_sig and macd_val < macd_sig: short_s += 15
    elif macd_val < macd_sig and macd_hist < 0: short_s += 5
    
    # BB (10p)
    if bb_pct < 0.1: long_s += 10
    elif bb_pct < 0.25: long_s += 5
    if bb_pct > 0.9: short_s += 10
    elif bb_pct > 0.75: short_s += 5
    
    # ADX + DI (10p)
    if adx > 25:
        if di_plus > di_minus: long_s += 10
        else: short_s += 10
    
    # StochRSI (10p)
    if stoch_k < 20: long_s += 10
    if stoch_k > 80: short_s += 10
    
    # Volume (5p)
    if vol_sma > 0 and vol > vol_sma * 1.3:
        is_green = row['close'] > row['open']
        if is_green: long_s += 5
        else: short_s += 5
    
    # BTC bias etkisi
    if btc_bias == 'BULL':
        long_s += 15
        short_s -= 10
    elif btc_bias == 'BEAR':
        short_s += 15
        long_s -= 10
    
    if long_s > short_s and long_s >= 25:
        return 'LONG', long_s, min(long_s / 100, 1.0)
    elif short_s > long_s and short_s >= 25:
        return 'SHORT', short_s, min(short_s / 100, 1.0)
    else:
        # Zorunlu giris - BTC yonune gore
        if btc_bias == 'BULL':
            return 'LONG', max(long_s, 15), 0.1
        elif btc_bias == 'BEAR':
            return 'SHORT', max(short_s, 15), 0.1
        else:
            return ('LONG' if long_s >= short_s else 'SHORT'), max(long_s, short_s, 10), 0.05


def run_sol_test():
    sep = "=" * 80
    line = "-" * 80
    
    print(sep)
    print("  SOL AGRESIF TEST - Gunde 5 Islem, 10x, Tum Bakiye")
    print(sep)
    print(f"  Tarih    : {BACKTEST_START.strftime('%Y-%m-%d')} -> {BACKTEST_END.strftime('%Y-%m-%d')}")
    print(f"  Bakiye   : ${INITIAL_BALANCE}")
    print(f"  Kaldirac : {LEVERAGE}x (sabit)")
    print(f"  Risk     : TUM BAKIYE her islemde")
    print(f"  Hedef    : Gunde min {MIN_TRADES_PER_DAY} islem")
    print(f"  SL       : {SL_ATR_MULT}x ATR (~%{SL_ATR_MULT*1.5:.1f} fiyat)")
    print(f"  TP       : Partial - TP1(%50), TP2(%30), TP3(%20)")
    print(sep)
    
    # BTC yukle
    print("\n  [BTC] Yukleniyor...")
    btc_df = load_btc()
    print(f"  [OK] {len(btc_df)} mum")
    
    # SOL yukle
    sol_file = os.path.join(DATA_FOLDER, "SOL_USDT_USDT.csv")
    df = pd.read_csv(sol_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df[(df['timestamp'] >= BACKTEST_START) & (df['timestamp'] <= BACKTEST_END)]
    df = df.reset_index(drop=True)
    print(f"  [SOL] {len(df)} mum yuklendi")
    
    if len(df) < 100:
        print("  [X] Yeterli veri yok!")
        return
    
    df = calculate_indicators(df)
    print(f"  [OK] Indikatorler hesaplandi\n")
    
    # ==========================================
    # SIMULASYON
    # ==========================================
    balance = float(INITIAL_BALANCE)
    trades = []
    daily_counts = defaultdict(int)
    
    in_position = False
    pos_dir = None
    entry_price = 0
    entry_time = None
    entry_idx = 0
    sl_price = 0
    tp1_price = tp2_price = tp3_price = 0
    tp1_hit = tp2_hit = False
    remaining = 1.0
    trade_balance = 0  # Bu islem icin kullanilan bakiye
    
    cooldown_until = -1
    
    for i in range(60, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        price = float(row['close'])
        high = float(row['high'])
        low = float(row['low'])
        ts = row['timestamp']
        atr = float(row['atr']) if pd.notna(row['atr']) and row['atr'] > 0 else price * 0.015
        
        today = ts.strftime('%Y-%m-%d')
        
        # Bakiye bittiyse dur
        if balance <= 1:
            print(f"  [!!] LIKIDE OLDU: ${balance:.2f}")
            break
        
        if in_position:
            candles = i - entry_idx
            
            # MAX HOLD: 16 mum = 4 saat
            if candles >= 16:
                if pos_dir == 'LONG':
                    pnl_pct = ((price - entry_price) / entry_price) * 100 * remaining * LEVERAGE
                else:
                    pnl_pct = ((entry_price - price) / entry_price) * 100 * remaining * LEVERAGE
                pnl_pct = max(pnl_pct, MAX_LOSS_PER_TRADE)
                dollar = trade_balance * (pnl_pct / 100)
                balance += dollar
                trades.append({
                    'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                    'entry': entry_price, 'exit': price,
                    'sl': sl_price, 'tp1': tp1_price,
                    'pnl_pct': pnl_pct, 'pnl_usd': dollar,
                    'balance': balance, 'result': f'TIMEOUT {"(TP1+)" if tp1_hit else ""}'
                })
                daily_counts[today] += 0  # zaten sayildi
                in_position = False
                cooldown_until = i + 4  # 1 saat cooldown
                continue
            
            # STOP LOSS
            sl_hit = False
            if pos_dir == 'LONG' and low <= sl_price:
                sl_hit = True
                exit_p = sl_price
            elif pos_dir == 'SHORT' and high >= sl_price:
                sl_hit = True
                exit_p = sl_price
            
            if sl_hit:
                if pos_dir == 'LONG':
                    pnl_pct = ((exit_p - entry_price) / entry_price) * 100 * remaining * LEVERAGE
                else:
                    pnl_pct = ((entry_price - exit_p) / entry_price) * 100 * remaining * LEVERAGE
                pnl_pct = max(pnl_pct, MAX_LOSS_PER_TRADE)
                dollar = trade_balance * (pnl_pct / 100)
                balance += dollar
                result = 'STOP LOSS' if not tp1_hit else 'TRAILING (TP1+)'
                trades.append({
                    'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                    'entry': entry_price, 'exit': exit_p,
                    'sl': sl_price, 'tp1': tp1_price,
                    'pnl_pct': pnl_pct, 'pnl_usd': dollar,
                    'balance': balance, 'result': result
                })
                in_position = False
                cooldown_until = i + 6  # Kayiptan sonra 1.5 saat cooldown
                continue
            
            # PARTIAL TP
            if pos_dir == 'LONG':
                if not tp1_hit and high >= tp1_price:
                    tp1_hit = True
                    pnl = ((tp1_price - entry_price) / entry_price) * 100 * TP1_CLOSE * LEVERAGE
                    dollar = trade_balance * (pnl / 100)
                    balance += dollar
                    remaining = 1.0 - TP1_CLOSE
                    # Trailing SL: entry'ye cek
                    sl_price = entry_price + (tp1_price - entry_price) * 0.3
                    trades.append({
                        'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                        'entry': entry_price, 'exit': tp1_price,
                        'sl': sl_price, 'tp1': tp1_price,
                        'pnl_pct': pnl, 'pnl_usd': dollar,
                        'balance': balance, 'result': 'TP1'
                    })
                
                if tp1_hit and not tp2_hit and high >= tp2_price:
                    tp2_hit = True
                    pnl = ((tp2_price - entry_price) / entry_price) * 100 * TP2_CLOSE * LEVERAGE
                    dollar = trade_balance * (pnl / 100)
                    balance += dollar
                    remaining = TP3_CLOSE
                    sl_price = tp1_price  # SL'yi TP1'e cek
                    trades.append({
                        'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                        'entry': entry_price, 'exit': tp2_price,
                        'sl': sl_price, 'tp1': tp1_price,
                        'pnl_pct': pnl, 'pnl_usd': dollar,
                        'balance': balance, 'result': 'TP2'
                    })
                
                if tp2_hit and high >= tp3_price:
                    pnl = ((tp3_price - entry_price) / entry_price) * 100 * TP3_CLOSE * LEVERAGE
                    dollar = trade_balance * (pnl / 100)
                    balance += dollar
                    trades.append({
                        'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                        'entry': entry_price, 'exit': tp3_price,
                        'sl': sl_price, 'tp1': tp1_price,
                        'pnl_pct': pnl, 'pnl_usd': dollar,
                        'balance': balance, 'result': 'TP3'
                    })
                    in_position = False
                    cooldown_until = i + 2  # Kazanctan sonra kisa cooldown
                    continue
            
            else:  # SHORT
                if not tp1_hit and low <= tp1_price:
                    tp1_hit = True
                    pnl = ((entry_price - tp1_price) / entry_price) * 100 * TP1_CLOSE * LEVERAGE
                    dollar = trade_balance * (pnl / 100)
                    balance += dollar
                    remaining = 1.0 - TP1_CLOSE
                    sl_price = entry_price - (entry_price - tp1_price) * 0.3
                    trades.append({
                        'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                        'entry': entry_price, 'exit': tp1_price,
                        'sl': sl_price, 'tp1': tp1_price,
                        'pnl_pct': pnl, 'pnl_usd': dollar,
                        'balance': balance, 'result': 'TP1'
                    })
                
                if tp1_hit and not tp2_hit and low <= tp2_price:
                    tp2_hit = True
                    pnl = ((entry_price - tp2_price) / entry_price) * 100 * TP2_CLOSE * LEVERAGE
                    dollar = trade_balance * (pnl / 100)
                    balance += dollar
                    remaining = TP3_CLOSE
                    sl_price = tp1_price
                    trades.append({
                        'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                        'entry': entry_price, 'exit': tp2_price,
                        'sl': sl_price, 'tp1': tp1_price,
                        'pnl_pct': pnl, 'pnl_usd': dollar,
                        'balance': balance, 'result': 'TP2'
                    })
                
                if tp2_hit and low <= tp3_price:
                    pnl = ((entry_price - tp3_price) / entry_price) * 100 * TP3_CLOSE * LEVERAGE
                    dollar = trade_balance * (pnl / 100)
                    balance += dollar
                    trades.append({
                        'time': entry_time, 'exit_time': ts, 'dir': pos_dir,
                        'entry': entry_price, 'exit': tp3_price,
                        'sl': sl_price, 'tp1': tp1_price,
                        'pnl_pct': pnl, 'pnl_usd': dollar,
                        'balance': balance, 'result': 'TP3'
                    })
                    in_position = False
                    cooldown_until = i + 2
                    continue
        
        else:
            # YENI GIRIS
            if i < cooldown_until:
                continue
            
            # Gunde 5 islem zorunlu - ama akilli giris
            btc_bias, btc_str = get_btc_bias(btc_df, ts)
            direction, score, confidence = score_entry(row, prev, btc_bias)
            
            # Gunde kac islem yaptik?
            today_count = daily_counts[today]
            
            # Skor dusukse ve gun bitmemisse bekle
            hour = ts.hour
            remaining_hours = 24 - hour
            remaining_slots = MIN_TRADES_PER_DAY - today_count
            
            # Giris karari
            should_enter = False
            
            if score >= 50:
                # Guclu sinyal - hemen gir
                should_enter = True
            elif score >= 30 and today_count < 3:
                # Orta sinyal, henuz az islem yapmisiz
                should_enter = True
            elif remaining_slots > 0 and remaining_hours <= remaining_slots * 2:
                # Gun bitiyor, yeterli islem yapilmamis - mecburi gir
                should_enter = True
            elif score >= 25 and today_count < MIN_TRADES_PER_DAY:
                # Minimum sinyal var ve gunde 5'e ulasmamis
                # Her 4 mumda (1 saatte) bir giris firsati degerlendir
                if i % 4 == 0:
                    should_enter = True
            
            if should_enter and balance > 1:
                in_position = True
                pos_dir = direction
                entry_price = price
                entry_time = ts
                entry_idx = i
                trade_balance = balance  # TUM BAKIYE
                tp1_hit = tp2_hit = False
                remaining = 1.0
                daily_counts[today] += 1
                
                risk = atr * SL_ATR_MULT
                
                if direction == 'LONG':
                    sl_price = entry_price - risk
                    tp1_price = entry_price + risk * TP1_RR
                    tp2_price = entry_price + risk * TP2_RR
                    tp3_price = entry_price + risk * TP3_RR
                else:
                    sl_price = entry_price + risk
                    tp1_price = entry_price - risk * TP1_RR
                    tp2_price = entry_price - risk * TP2_RR
                    tp3_price = entry_price - risk * TP3_RR
    
    # Acik pozisyonu kapat
    if in_position and balance > 0:
        last = df.iloc[-1]
        p = float(last['close'])
        if pos_dir == 'LONG':
            pnl_pct = ((p - entry_price) / entry_price) * 100 * remaining * LEVERAGE
        else:
            pnl_pct = ((entry_price - p) / entry_price) * 100 * remaining * LEVERAGE
        pnl_pct = max(pnl_pct, MAX_LOSS_PER_TRADE)
        dollar = trade_balance * (pnl_pct / 100)
        balance += dollar
        trades.append({
            'time': entry_time, 'exit_time': last['timestamp'], 'dir': pos_dir,
            'entry': entry_price, 'exit': p,
            'sl': sl_price, 'tp1': tp1_price,
            'pnl_pct': pnl_pct, 'pnl_usd': dollar,
            'balance': balance, 'result': 'CLOSE'
        })
    
    # ==========================================
    # SONUCLAR
    # ==========================================
    print(sep)
    print("  SOL 10x AGRESIF - ISLEM TABLOSU")
    print(sep)
    print(f"  {'#':>3} {'Yon':5} {'Giris':>14} {'Cikis':>14} {'Entry':>10} {'Exit':>10} {'PnL%':>7} {'PnL$':>8} {'Bakiye':>9} {'Sonuc'}")
    print(line)
    
    n = 0
    for t in trades:
        n += 1
        d = "[L]" if t['dir'] == 'LONG' else "[S]"
        tag = "[+]" if t['pnl_usd'] > 0 else "[-]"
        print(f"  {n:>3} {d:5} {t['time'].strftime('%m-%d %H:%M'):>14} {t['exit_time'].strftime('%m-%d %H:%M'):>14} {t['entry']:>10.2f} {t['exit']:>10.2f} {t['pnl_pct']:>+6.1f}% {tag}{abs(t['pnl_usd']):>7.2f} ${t['balance']:>8.2f} {t['result']}")
    
    # Ozet
    print("\n" + sep)
    print("  SONUC")
    print(sep)
    
    if not trades:
        print("  Hic islem yok!")
        return
    
    wins = [t for t in trades if t['pnl_usd'] > 0]
    losses = [t for t in trades if t['pnl_usd'] <= 0]
    longs = [t for t in trades if t['dir'] == 'LONG']
    shorts = [t for t in trades if t['dir'] == 'SHORT']
    
    total_pnl = balance - INITIAL_BALANCE
    wr = len(wins) / len(trades) * 100 if trades else 0
    
    peak = INITIAL_BALANCE
    max_dd = 0
    running = INITIAL_BALANCE
    for t in trades:
        running = t['balance']
        if running > peak: peak = running
        dd = (peak - running) / peak * 100 if peak > 0 else 0
        if dd > max_dd: max_dd = dd
    
    avg_win = np.mean([t['pnl_usd'] for t in wins]) if wins else 0
    avg_loss = np.mean([t['pnl_usd'] for t in losses]) if losses else 0
    gross_win = sum(t['pnl_usd'] for t in wins) if wins else 0
    gross_loss = abs(sum(t['pnl_usd'] for t in losses)) if losses else 1
    
    print(f"  Baslangic  : ${INITIAL_BALANCE:.2f}")
    print(f"  Final      : ${balance:.2f}")
    print(f"  PnL        : ${total_pnl:+.2f} ({total_pnl/INITIAL_BALANCE*100:+.1f}%)")
    print(line)
    print(f"  Islem      : {len(trades)} ({len(wins)}W / {len(losses)}L) - WR: {wr:.1f}%")
    print(f"  LONG       : {len(longs)} islem (${sum(t['pnl_usd'] for t in longs):+.2f})")
    print(f"  SHORT      : {len(shorts)} islem (${sum(t['pnl_usd'] for t in shorts):+.2f})")
    print(f"  Avg W/L    : ${avg_win:+.2f} / ${avg_loss:.2f}")
    print(f"  Peak       : ${peak:.2f}")
    print(f"  Max DD     : {max_dd:.1f}%")
    print(f"  PF         : {gross_win/gross_loss:.2f}")
    
    # Gunluk
    print(f"\n{line}")
    print("  GUNLUK BREAKDOWN")
    print(line)
    daily = defaultdict(lambda: {'n': 0, 'pnl': 0, 'bal': 0})
    for t in trades:
        day = t['time'].strftime('%Y-%m-%d %A')
        daily[day]['n'] += 1
        daily[day]['pnl'] += t['pnl_usd']
        daily[day]['bal'] = t['balance']
    
    for day in sorted(daily.keys()):
        d = daily[day]
        tag = "[+]" if d['pnl'] >= 0 else "[-]"
        print(f"  {tag} {day}: {d['n']:>2} islem | PnL: ${d['pnl']:>+8.2f} | Bakiye: ${d['bal']:>9.2f}")
    
    print(f"\n  Gunde Ort Islem: {len(trades)/max(len(daily),1):.1f}")
    print(sep)


if __name__ == "__main__":
    run_sol_test()
