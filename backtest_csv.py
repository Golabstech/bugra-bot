import pandas as pd
import pandas_ta as ta
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')
pd.set_option('future.no_silent_downcasting', True)

# ==========================================
# ⚙️ BACKTEST AYARLARI
# ==========================================
DATA_FOLDER = "backtest_data"
INITIAL_BALANCE = 1000
POSITION_SIZE_PCT = 10
LEVERAGE = 10
MAKER_FEE = 0.0002
TAKER_FEE = 0.0005

# 📅 TARİH ARALIĞI (değiştirilebilir)
BACKTEST_START = datetime(2026, 1, 25, 0, 0, 0)
BACKTEST_END = datetime(2026, 2, 8, 23, 59, 59)

# 🎯 TEK COİN TEST (None = tüm coinler)
SINGLE_COIN = "HBAR/USDT:USDT"  # Test edilecek coin

# 📋 İŞLEM DETAYLARI GÖSTER
SHOW_TRADE_DETAILS = True

# ⚡ STRATEJİ FİLTRELERİ
SCORE_THRESHOLD = 80
MIN_WIN_RATE = 75
COOLDOWN_CANDLES = 8
MAX_TRADES_PER_COIN = 20  # Dönem başına

# 🎯 VOLATİLİTE FİLTRESİ
MAX_ATR_PERCENT = 5.0
MIN_ATR_PERCENT = 0.5

# 🎯 PARTIAL TP ORANLARI
TP1_CLOSE_PCT = 0.30
TP2_CLOSE_PCT = 0.30
TP3_CLOSE_PCT = 0.40

# 🎯 SL VE TP ÇARPANLARI
SL_ATR_MULT = 2.5
TP1_RR = 1.5
TP2_RR = 2.5
TP3_RR = 4.0

TRAILING_STOP = True
PARTIAL_TP = True

# ==========================================
# 📊 İNDİKATÖR HESAPLAMA
# ==========================================
def calculate_indicators(df):
    """İndikatörleri hesapla"""
    df = df.copy()
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    df['sma50'] = ta.sma(df['close'], length=50)
    df['rsi'] = ta.rsi(df['close'], length=14)
    
    macd = ta.macd(df['close'])
    if macd is not None:
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 1]
    else:
        df['macd'] = df['macd_signal'] = 0
    
    bb = ta.bbands(df['close'], length=20, std=2)
    if bb is not None:
        df['bb_lower'] = bb.iloc[:, 0]
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
    return df

def calculate_short_score(row):
    """SHORT puanı hesapla"""
    score = 0
    reasons = []
    
    price = float(row['close'])
    adx = float(row['adx']) if pd.notna(row['adx']) else 0
    di_plus = float(row['di_plus']) if pd.notna(row['di_plus']) else 0
    di_minus = float(row['di_minus']) if pd.notna(row['di_minus']) else 0
    ema9 = float(row['ema9']) if pd.notna(row['ema9']) else price
    ema21 = float(row['ema21']) if pd.notna(row['ema21']) else price
    sma50 = float(row['sma50']) if pd.notna(row['sma50']) else price
    rsi = float(row['rsi']) if pd.notna(row['rsi']) else 50
    macd_val = float(row['macd']) if pd.notna(row['macd']) else 0
    macd_sig = float(row['macd_signal']) if pd.notna(row['macd_signal']) else 0
    bb_pct = float(row['bb_pct']) if pd.notna(row['bb_pct']) else 0.5
    stoch_k = float(row['stoch_k']) if pd.notna(row['stoch_k']) else 50
    mfi = float(row['mfi']) if pd.notna(row['mfi']) else 50
    
    # ADX + DI
    if adx > 25 and di_minus > di_plus:
        score += 30
        reasons.append(f"ADX({adx:.0f})+DI-")
    elif di_minus > di_plus:
        score += 15
        reasons.append("DI->DI+")
    
    # EMA
    if ema9 < ema21 < sma50:
        score += 25
        reasons.append("EMA Bearish")
    elif ema9 < ema21:
        score += 15
        reasons.append("EMA9<21")
    
    # RSI
    if rsi > 70:
        score += 25
        reasons.append(f"RSI({rsi:.0f})")
    elif rsi > 60:
        score += 15
        reasons.append(f"RSI({rsi:.0f})")
    
    # MACD
    if macd_val < macd_sig:
        score += 20
        reasons.append("MACD-")
    
    # Bollinger
    if bb_pct > 0.95:
        score += 25
        reasons.append(f"BB({bb_pct*100:.0f}%)")
    elif bb_pct > 0.8:
        score += 15
        reasons.append(f"BB({bb_pct*100:.0f}%)")
    
    # StochRSI
    if stoch_k > 80:
        score += 20
        reasons.append(f"Stoch({stoch_k:.0f})")
    
    # MFI
    if mfi > 80:
        score += 15
        reasons.append(f"MFI({mfi:.0f})")
    
    return score, reasons

# ==========================================
# 🔄 BACKTEST FONKSİYONU
# ==========================================
def backtest_coin(symbol, df):
    """Tek coin için backtest"""
    trades = []
    in_position = False
    entry_price = 0
    entry_time = None
    stop_loss = 0
    original_stop = 0
    tp1 = tp2 = tp3 = 0
    tp1_hit = tp2_hit = False
    position_remaining = 1.0
    last_exit_candle = -999
    trade_count = 0
    
    # Volatilite kontrolü
    if len(df) > 50:
        first_atr = df.iloc[50]['atr'] if pd.notna(df.iloc[50]['atr']) else 0
        first_price = df.iloc[50]['close']
        atr_pct = (first_atr / first_price) * 100 if first_price > 0 else 0
        
        if atr_pct > MAX_ATR_PERCENT or atr_pct < MIN_ATR_PERCENT:
            return []
    
    for i in range(50, len(df)):
        row = df.iloc[i]
        current_price = float(row['close'])
        current_time = row['timestamp']
        high = float(row['high'])
        low = float(row['low'])
        atr = float(row['atr']) if pd.notna(row['atr']) else current_price * 0.02
        
        if in_position:
            # Trailing Stop
            if TRAILING_STOP:
                if tp1_hit and not tp2_hit:
                    new_stop = entry_price + (original_stop - entry_price) * 0.5
                    if stop_loss > new_stop:
                        stop_loss = new_stop
                if tp2_hit:
                    if stop_loss > entry_price:
                        stop_loss = entry_price
            
            # Stop Loss kontrol
            if high >= stop_loss:
                pnl_pct = ((entry_price - stop_loss) / entry_price) * 100 * position_remaining
                result_text = 'STOP LOSS'
                if tp1_hit: result_text = 'TRAILING (TP1+)'
                if tp2_hit: result_text = 'TRAILING (TP2+)'
                
                trades.append({
                    'symbol': symbol, 'entry_time': entry_time, 'exit_time': current_time,
                    'entry_price': entry_price, 'exit_price': stop_loss,
                    'pnl_pct': pnl_pct, 'result': result_text
                })
                in_position = False
                last_exit_candle = i
                position_remaining = 1.0
                continue
            
            # Partial TP
            if PARTIAL_TP:
                if not tp1_hit and low <= tp1:
                    tp1_hit = True
                    partial_pnl = ((entry_price - tp1) / entry_price) * 100 * TP1_CLOSE_PCT
                    trades.append({
                        'symbol': symbol, 'entry_time': entry_time, 'exit_time': current_time,
                        'entry_price': entry_price, 'exit_price': tp1,
                        'pnl_pct': partial_pnl, 'result': f'TP1 ({int(TP1_CLOSE_PCT*100)}%)'
                    })
                    position_remaining = 1.0 - TP1_CLOSE_PCT
                
                if tp1_hit and not tp2_hit and low <= tp2:
                    tp2_hit = True
                    partial_pnl = ((entry_price - tp2) / entry_price) * 100 * TP2_CLOSE_PCT
                    trades.append({
                        'symbol': symbol, 'entry_time': entry_time, 'exit_time': current_time,
                        'entry_price': entry_price, 'exit_price': tp2,
                        'pnl_pct': partial_pnl, 'result': f'TP2 ({int(TP2_CLOSE_PCT*100)}%)'
                    })
                    position_remaining = TP3_CLOSE_PCT
                
                if tp2_hit and low <= tp3:
                    partial_pnl = ((entry_price - tp3) / entry_price) * 100 * TP3_CLOSE_PCT
                    trades.append({
                        'symbol': symbol, 'entry_time': entry_time, 'exit_time': current_time,
                        'entry_price': entry_price, 'exit_price': tp3,
                        'pnl_pct': partial_pnl, 'result': f'TP3 ({int(TP3_CLOSE_PCT*100)}%)'
                    })
                    in_position = False
                    last_exit_candle = i
                    position_remaining = 1.0
                    continue
        else:
            if i - last_exit_candle < COOLDOWN_CANDLES:
                continue
            if trade_count >= MAX_TRADES_PER_COIN:
                continue
            
            score, reasons = calculate_short_score(row)
            
            win_rate = 50
            if score >= 100: win_rate += 20
            elif score >= 80: win_rate += 15
            elif score >= 70: win_rate += 10
            elif score >= 60: win_rate += 5
            
            if len(reasons) >= 5: win_rate += 10
            elif len(reasons) >= 4: win_rate += 5
            
            if score >= SCORE_THRESHOLD and win_rate >= MIN_WIN_RATE:
                in_position = True
                entry_price = current_price
                entry_time = current_time
                trade_count += 1
                
                risk = atr * SL_ATR_MULT
                original_stop = entry_price + risk
                stop_loss = original_stop
                tp1 = entry_price - (risk * TP1_RR)
                tp2 = entry_price - (risk * TP2_RR)
                tp3 = entry_price - (risk * TP3_RR)
                tp1_hit = tp2_hit = False
                position_remaining = 1.0
    
    # Açık pozisyonu kapat
    if in_position:
        last_row = df.iloc[-1]
        exit_price = float(last_row['close'])
        pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * position_remaining
        trades.append({
            'symbol': symbol, 'entry_time': entry_time, 'exit_time': last_row['timestamp'],
            'entry_price': entry_price, 'exit_price': exit_price,
            'pnl_pct': pnl_pct, 'result': 'DÖNEM SONU'
        })
    
    return trades

# ==========================================
# 🚀 ANA BACKTEST
# ==========================================
def run_backtest():
    """CSV'lerden backtest çalıştır"""
    print("=" * 70)
    print("🚀 HIZLI BACKTEST (CSV'DEN)")
    print("=" * 70)
    print(f"📅 Tarih Aralığı: {BACKTEST_START.strftime('%Y-%m-%d')} - {BACKTEST_END.strftime('%Y-%m-%d')}")
    print(f"💰 Başlangıç: ${INITIAL_BALANCE} | Kaldıraç: {LEVERAGE}x")
    if SINGLE_COIN:
        print(f"🎯 Sadece: {SINGLE_COIN}")
    print("-" * 70)
    print(f"⚙️ Score: {SCORE_THRESHOLD} | Win Rate: {MIN_WIN_RATE}%")
    print(f"🎯 SL: ATR x {SL_ATR_MULT} | TP1: 1:{TP1_RR} | TP2: 1:{TP2_RR} | TP3: 1:{TP3_RR}")
    print("=" * 70)
    
    # Coin listesi oku
    coin_list_file = f"{DATA_FOLDER}/_coin_list.csv"
    if not os.path.exists(coin_list_file):
        print(f"❌ Coin listesi bulunamadı! Önce veri_cek.py çalıştırın.")
        return
    
    coin_list = pd.read_csv(coin_list_file)
    
    # Tek coin filtresi
    if SINGLE_COIN:
        coin_list = coin_list[coin_list['symbol'] == SINGLE_COIN]
        if len(coin_list) == 0:
            print(f"❌ {SINGLE_COIN} verisi bulunamadı!")
            return
    
    print(f"\n📋 {len(coin_list)} coin yükleniyor...\n")
    
    all_trades = []
    analyzed = 0
    
    for i, row in coin_list.iterrows():
        symbol = row['symbol']
        filename = row['file']
        
        print(f"\r[{i+1}/{len(coin_list)}] {symbol} analiz ediliyor...", end="        ")
        
        if not os.path.exists(filename):
            continue
        
        # CSV'den oku
        df = pd.read_csv(filename)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Tarih filtresi
        df = df[(df['timestamp'] >= BACKTEST_START) & (df['timestamp'] <= BACKTEST_END)]
        
        if len(df) < 50:
            continue
        
        # İndikatörler
        df = calculate_indicators(df)
        
        # Backtest
        trades = backtest_coin(symbol, df)
        if trades:
            all_trades.extend(trades)
        
        analyzed += 1
    
    print(f"\n\n✅ {analyzed} coin analiz edildi")
    
    if not all_trades:
        print("\n❌ Hiç işlem bulunamadı!")
        return
    
    # İşlem detayları
    if SHOW_TRADE_DETAILS:
        print("\n" + "=" * 70)
        print("📋 İŞLEM DETAYLARI")
        print("=" * 70)
        
        for i, t in enumerate(all_trades, 1):
            pnl = t['pnl_pct']
            lev_pnl = pnl * LEVERAGE
            
            if pnl > 0:
                status = "✅"
            elif pnl < 0:
                status = "❌"
            else:
                status = "➖"
            
            entry_time = t['entry_time'].strftime('%m/%d %H:%M') if hasattr(t['entry_time'], 'strftime') else str(t['entry_time'])[:16]
            exit_time = t['exit_time'].strftime('%m/%d %H:%M') if hasattr(t['exit_time'], 'strftime') else str(t['exit_time'])[:16]
            
            print(f"{status} #{i:02d} | {entry_time} → {exit_time} | ${t['entry_price']:.4f} → ${t['exit_price']:.4f} | {pnl:+.2f}% ({lev_pnl:+.1f}%x) | {t['result']}")
    
    # Sonuçlar
    print("\n" + "=" * 70)
    print("📊 İŞLEM ÖZETİ")
    print("=" * 70)
    
    tp1_count = sum(1 for t in all_trades if 'TP1' in t['result'])
    tp2_count = sum(1 for t in all_trades if 'TP2' in t['result'])
    tp3_count = sum(1 for t in all_trades if 'TP3' in t['result'])
    sl_count = sum(1 for t in all_trades if 'STOP' in t['result'])
    trailing_count = sum(1 for t in all_trades if 'TRAILING' in t['result'])
    
    wins = [t for t in all_trades if t['pnl_pct'] > 0]
    losses = [t for t in all_trades if t['pnl_pct'] < 0]
    
    print(f"🎯 TP1: {tp1_count} | TP2: {tp2_count} | TP3: {tp3_count}")
    print(f"❌ Stop Loss: {sl_count} | Trailing: {trailing_count}")
    
    if wins:
        avg_win = sum(t['pnl_pct'] for t in wins) / len(wins)
        print(f"✅ Kazançlı: {len(wins)} | Ort: {avg_win:.2f}%")
    
    if losses:
        avg_loss = sum(t['pnl_pct'] for t in losses) / len(losses)
        print(f"❌ Kayıplı: {len(losses)} | Ort: {avg_loss:.2f}%")
    
    if wins and losses:
        rr = abs(avg_win / avg_loss)
        print(f"📈 Risk/Reward: 1:{rr:.2f}")
    
    # Final bakiye
    final_balance = INITIAL_BALANCE
    for trade in all_trades:
        pnl = trade['pnl_pct'] * LEVERAGE
        position_size = final_balance * (POSITION_SIZE_PCT / 100)
        profit = position_size * (pnl / 100)
        fee = position_size * LEVERAGE * (MAKER_FEE + TAKER_FEE)
        final_balance += profit - fee
    
    profit_loss = final_balance - INITIAL_BALANCE
    win_rate = (len(wins) / len(all_trades) * 100) if all_trades else 0
    
    print("\n" + "=" * 70)
    print("💰 BACKTEST SONUCU")
    print("=" * 70)
    print(f"📈 Toplam İşlem: {len(all_trades)}")
    print(f"📊 Win Rate: {win_rate:.1f}%")
    print(f"💵 Başlangıç: ${INITIAL_BALANCE:.2f}")
    print(f"💵 Final: ${final_balance:.2f}")
    print(f"{'📈' if profit_loss >= 0 else '📉'} Kar/Zarar: ${profit_loss:+.2f} ({profit_loss/INITIAL_BALANCE*100:+.2f}%)")
    print("=" * 70)
    
    # En iyi/kötü işlemler
    if all_trades:
        sorted_trades = sorted(all_trades, key=lambda x: x['pnl_pct'], reverse=True)
        print("\n🏆 EN İYİ 3 İŞLEM:")
        for t in sorted_trades[:3]:
            print(f"   {t['symbol']}: {t['pnl_pct']:.2f}% ({t['result']})")
        
        print("\n💀 EN KÖTÜ 3 İŞLEM:")
        for t in sorted_trades[-3:]:
            print(f"   {t['symbol']}: {t['pnl_pct']:.2f}% ({t['result']})")

if __name__ == "__main__":
    import time
    start = time.time()
    run_backtest()
    print(f"\n⏱️ Süre: {time.time() - start:.1f} saniye")
