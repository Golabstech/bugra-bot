import pandas as pd
import pandas_ta as ta
import warnings
import os
import random
import numpy as np
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

warnings.filterwarnings('ignore')
pd.set_option('future.no_silent_downcasting', True)

# ==========================================
# ⚙️ BACKTEST AYARLARI
# ==========================================
DATA_FOLDER = "backtest_data"
INITIAL_BALANCE = 1000
POSITION_SIZE_PCT = 10
LEVERAGE = 5
MAKER_FEE = 0.0002
TAKER_FEE = 0.0005

# 📅 TARİH ARALIĞI (Final Test: 90 Günlük Karma Senaryo)
BACKTEST_START = datetime(2025, 12, 10, 0, 0, 0)
BACKTEST_END = datetime(2026, 2, 10, 23, 59, 59)

# 🎲 MONTE CARLO AYARLARI
RUN_MONTE_CARLO = False  # Doğrulama için True yapın
MONTE_CARLO_SIMULATIONS = 5000

# 🎯 TEK COİN TEST (None = tüm coinler)
SINGLE_COIN = None  # Tüm coinler test edilsin

# 📋 İŞLEM DETAYLARI GÖSTER (Kapsamlı testte False olması daha iyi)
SHOW_TRADE_DETAILS = False

# ⚡ STRATEJİ FİLTRELERİ
SCORE_THRESHOLD = 80
MIN_WIN_RATE = 75
COOLDOWN_CANDLES = 8
MAX_TRADES_PER_COIN = 20  # Dönem başına

# 🎯 VOLATİLİTE FİLTRESİ
MAX_ATR_PERCENT = 4.5   # Biraz daha esnek volatilite
MIN_ATR_PERCENT = 0.5
HARD_STOP_LOSS_PCT = 7.0 # %7'den fazla zarara ASLA izin verme (PIPPIN Koruması)

# 🎯 PARTIAL TP ORANLARI
TP1_CLOSE_PCT = 0.40  # Dengeli kâr realizasyonu
TP2_CLOSE_PCT = 0.30
TP3_CLOSE_PCT = 0.30

# 🎯 SL VE TP ÇARPANLARI
SL_ATR_MULT = 2.4   # Daha sıkı stop, daha iyi R/R
TP1_RR = 1.8        # Daha yüksek ilk hedef
TP2_RR = 2.8        
TP3_RR = 4.5

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
        df['macd_signal'] = macd.iloc[:, 2]  # Sinyal çizgisi index 2'dedir
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

def calculate_scores_vectorized(df):
    """Tüm tablonun puanlarını ve neden sayısını tek seferde hesapla"""
    n = len(df)
    scores = pd.Series(0, index=df.index)
    reason_counts = pd.Series(0, index=df.index)
    
    # Verileri al
    adx = df['adx'].values
    di_plus = df['di_plus'].values
    di_minus = df['di_minus'].values
    ema9 = df['ema9'].values
    ema21 = df['ema21'].values
    sma50 = df['sma50'].values
    rsi = df['rsi'].values
    macd_val = df['macd'].values
    macd_sig = df['macd_signal'].values
    bb_pct = df['bb_pct'].values
    stoch_k = df['stoch_k'].values
    mfi = df['mfi'].values

    # ADX + DI
    mask_adx1 = (adx > 25) & (di_minus > di_plus)
    scores += mask_adx1 * 30
    mask_adx2 = (~mask_adx1) & (di_minus > di_plus)
    scores += mask_adx2 * 15
    reason_counts += (di_minus > di_plus)
    
    # EMA - Trend Takibini Nötrle (Zarar ettiriyor, sadece izle)
    mask_ema_bear = (ema9 < ema21) & (ema21 < sma50)
    scores += mask_ema_bear * 0  # Puan verme
    reason_counts += mask_ema_bear
    
    # 🚀 SMA50 UZAKLIK (Overextension Bonus) - Daha Dengeli
    dist_sma50 = (df['close'] - df['sma50']) / df['sma50'] * 100
    mask_dist1 = (dist_sma50 > 4)
    mask_dist2 = (dist_sma50 > 2) & (~mask_dist1)
    scores += mask_dist1 * 25
    scores += mask_dist2 * 10
    reason_counts += mask_dist2 | mask_dist1
    
    # RSI
    mask_rsi = (rsi > 60)
    scores += (rsi > 80) * 30  # Aşırı şişme bonusu
    scores += ((rsi > 65) & (rsi <= 80)) * 20
    reason_counts += mask_rsi
    
    # MACD - Puanı düşür, ana tetikleyici olmasın
    mask_macd = (macd_val < macd_sig)
    scores += mask_macd * 5  # 20'den 5'e çekildi
    reason_counts += mask_macd
    
    # Bollinger
    mask_bb = (bb_pct > 0.8)
    scores += (bb_pct > 0.95) * 25
    scores += ((bb_pct > 0.8) & (bb_pct <= 0.95)) * 15
    reason_counts += mask_bb
    
    # StochRSI
    mask_stoch = (stoch_k > 80)
    scores += mask_stoch * 20
    reason_counts += mask_stoch
    
    # MFI
    mask_mfi = (mfi > 80)
    scores += mask_mfi * 15
    reason_counts += mask_mfi

    return scores.values, reason_counts.values

def get_detailed_reasons(row):
    """Sadece entry anında detaylı rapor için metinleri oluştur"""
    reasons = []
    adx = row['adx']
    di_plus = row['di_plus']
    di_minus = row['di_minus']
    ema9 = row['ema9']
    ema21 = row['ema21']
    sma50 = row['sma50']
    rsi = row['rsi']
    macd_val = row['macd']
    macd_sig = row['macd_signal']
    bb_pct = row['bb_pct']
    stoch_k = row['stoch_k']
    mfi = row['mfi']

    if adx > 25 and di_minus > di_plus: reasons.append(f"ADX({adx:.0f})+DI-")
    elif di_minus > di_plus: reasons.append("DI->DI+")
    
    if ema9 < ema21 < sma50: reasons.append("EMA Bearish")
    elif ema9 < ema21: reasons.append("EMA9<21")
    
    if rsi > 70: reasons.append(f"RSI({rsi:.0f})")
    elif rsi > 60: reasons.append(f"RSI({rsi:.0f})")
    
    if macd_val < macd_sig: reasons.append("MACD-")
    
    if bb_pct > 0.95: reasons.append(f"BB({bb_pct*100:.0f}%)")
    elif bb_pct > 0.8: reasons.append(f"BB({bb_pct*100:.0f}%)")
    
    if stoch_k > 80: reasons.append(f"Stoch({stoch_k:.0f})")
    if mfi > 80: reasons.append(f"MFI({mfi:.0f})")
    
    return reasons

# ==========================================
# 🔄 BACKTEST FONKSİYONU
# ==========================================
def backtest_coin(symbol, df):
    """Tek coin için backtest - Ultra Hızlı Numpy Versiyonu"""
    # Verileri Numpy array'lere çevir (Müthiş hız artışı sağlar)
    timestamps = df['timestamp'].values
    close_arr = df['close'].values.astype(float)
    high_arr = df['high'].values.astype(float)
    low_arr = df['low'].values.astype(float)
    atr_arr = df['atr'].values.astype(float)
    sma50_arr = df['sma50'].values.astype(float)
    rsi_arr = df['rsi'].values.astype(float)
    macd_arr = df['macd'].values.astype(float)
    macd_sig_arr = df['macd_signal'].values.astype(float)
    
    # Puanları ve neden sayılarını tek seferde hesapla
    sc_values, rc_values = calculate_scores_vectorized(df)
    df['calculated_score'] = sc_values
    df['reason_count'] = rc_values
    
    score_arr = df['calculated_score'].values
    rc_arr = df['reason_count'].values
    
    trades = []
    in_position = False
    entry_price = 0.0
    entry_time = None
    stop_loss = 0.0
    original_stop = 0.0
    tp1 = tp2 = tp3 = 0.0
    tp1_hit = tp2_hit = False
    position_remaining = 1.0
    last_exit_candle = -999
    trade_count = 0
    consecutive_losses = 0
    block_until_candle = 0
    
    total_len = len(df)
    
    # Volatilite kontrolü (Numpy ile)
    if total_len > 50:
        atr_pct = (atr_arr[50] / close_arr[50]) * 100
        if atr_pct > MAX_ATR_PERCENT or atr_pct < MIN_ATR_PERCENT:
            return []

    for i in range(50, total_len):
        current_price = close_arr[i]
        
        if in_position:
            high = high_arr[i]
            low = low_arr[i]
            
            # Trailing Stop - Agresif Mod
            if TRAILING_STOP:
                if tp1_hit:
                    # TP1 gerçekleştikten sonra stopu anında Giriş Fiyatına (BE) çek.
                    # Bu, kârlı işlemlerin zarara dönmesini engeller.
                    if stop_loss > entry_price:
                        stop_loss = entry_price
                if tp2_hit:
                    # TP2 gerçekleştikten sonra stopu kâra kitle (Giriş - ATR/2)
                    new_stop = entry_price - (atr_arr[i] * 0.5)
                    if stop_loss > new_stop:
                        stop_loss = new_stop
            
            # Stop Loss kontrol
            if high >= stop_loss:
                pnl_pct = ((entry_price - stop_loss) / entry_price) * 100 * position_remaining
                if abs(pnl_pct) > HARD_STOP_LOSS_PCT:
                     pnl_pct = -HARD_STOP_LOSS_PCT
                     stop_loss = entry_price * (1 + HARD_STOP_LOSS_PCT/100)
                
                res = 'STOP LOSS'
                if tp1_hit: res = 'TRAILING (TP1+)'
                if tp2_hit: res = 'TRAILING (TP2+)'
                
                if pnl_pct < 0: consecutive_losses += 1
                else: consecutive_losses = 0
                
                if consecutive_losses >= 2:
                    block_until_candle = i + 16
                    consecutive_losses = 0
                
                trades.append({
                    'symbol': symbol, 'entry_time': entry_time, 'exit_time': timestamps[i],
                    'entry_price': entry_price, 'exit_price': stop_loss,
                    'pnl_pct': pnl_pct, 'result': res,
                    'reasons': entry_reasons
                })
                in_position = False
                last_exit_candle = i
                position_remaining = 1.0
                continue
            
            # Partial TP
            if PARTIAL_TP:
                if not tp1_hit and low <= tp1:
                    tp1_hit = True
                    trades.append({
                        'symbol': symbol, 'entry_time': entry_time, 'exit_time': timestamps[i],
                        'entry_price': entry_price, 'exit_price': tp1,
                        'pnl_pct': ((entry_price - tp1) / entry_price) * 100 * TP1_CLOSE_PCT, 
                        'result': f'TP1 ({int(TP1_CLOSE_PCT*100)}%)', 'reasons': entry_reasons
                    })
                    position_remaining = 1.0 - TP1_CLOSE_PCT
                
                if tp1_hit and not tp2_hit and low <= tp2:
                    tp2_hit = True
                    trades.append({
                        'symbol': symbol, 'entry_time': entry_time, 'exit_time': timestamps[i],
                        'entry_price': entry_price, 'exit_price': tp2,
                        'pnl_pct': ((entry_price - tp2) / entry_price) * 100 * TP2_CLOSE_PCT,
                        'result': f'TP2 ({int(TP2_CLOSE_PCT*100)}%)', 'reasons': entry_reasons
                    })
                    position_remaining = TP3_CLOSE_PCT
                
                if tp2_hit and low <= tp3:
                    trades.append({
                        'symbol': symbol, 'entry_time': entry_time, 'exit_time': timestamps[i],
                        'entry_price': entry_price, 'exit_price': tp3,
                        'pnl_pct': ((entry_price - tp3) / entry_price) * 100 * TP3_CLOSE_PCT,
                        'result': f'TP3 ({int(TP3_CLOSE_PCT*100)}%)', 'reasons': entry_reasons
                    })
                    in_position = False
                    last_exit_candle = i
                    continue
        else:
            if i - last_exit_candle < COOLDOWN_CANDLES: continue
            if trade_count >= MAX_TRADES_PER_COIN: continue
            if i < block_until_candle: continue
            
            score = score_arr[i]
            
            # Boğa Koruması
            sma50 = sma50_arr[i]
            rsi_curr = rsi_arr[i]
            rsi_prev = rsi_arr[i-1]
            macd_confirmed = macd_arr[i] < macd_sig_arr[i]
            
            is_bull = current_price > sma50
            if is_bull:
                final_threshold = SCORE_THRESHOLD + 10
                if macd_confirmed: score += 15
                if rsi_curr > 85 and rsi_curr >= rsi_prev: continue
            else:
                final_threshold = SCORE_THRESHOLD

            if score >= final_threshold:
                # Orijinal win_rate mantığını birebir uygula
                win_rate = 50
                if score >= 100: win_rate += 20
                elif score >= 80: win_rate += 15
                elif score >= 70: win_rate += 10
                elif score >= 60: win_rate += 5
                
                num_reasons = rc_arr[i]
                if num_reasons >= 5: win_rate += 10
                elif num_reasons >= 4: win_rate += 5
                
                if win_rate >= MIN_WIN_RATE:
                    atr = atr_arr[i]
                    atr_pct = (atr / current_price) * 100
                    if atr_pct > MAX_ATR_PERCENT or atr_pct < MIN_ATR_PERCENT: continue
                    
                    in_position = True
                    entry_price = current_price
                    entry_time = timestamps[i]
                    
                    # Detaylı nedenleri sadece entry anında getir (Hız kaybı olmaz)
                    entry_reasons = get_detailed_reasons(df.iloc[i])
                    
                    trade_count += 1
                    risk = atr * SL_ATR_MULT
                    original_stop = entry_price + risk
                    stop_loss = original_stop
                    tp1, tp2, tp3 = entry_price-(risk*TP1_RR), entry_price-(risk*TP2_RR), entry_price-(risk*TP3_RR)
                    tp1_hit = tp2_hit = False
    
    if in_position:
        exit_p = close_arr[-1]
        trades.append({'symbol': symbol, 'entry_time': entry_time, 'exit_time': timestamps[-1],
                       'entry_price': entry_price, 'exit_price': exit_p,
                       'pnl_pct': ((entry_price - exit_p) / entry_price) * 100 * position_remaining,
                       'result': 'DÖNEM SONU', 'reasons': entry_reasons})
    return trades
    
    # Açık pozisyonu kapat
    if in_position:
        last_row = df.iloc[-1]
        exit_price = float(last_row['close'])
        pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * position_remaining
        trades.append({
            'symbol': symbol, 'entry_time': entry_time, 'exit_time': last_row['timestamp'],
            'entry_price': entry_price, 'exit_price': exit_price,
            'pnl_pct': pnl_pct, 'result': 'DÖNEM SONU',
            'reasons': entry_reasons
        })
    
    return trades

# ==========================================
# � PARALEL WORKER FONKSİYONU
# ==========================================
def _process_coin(args):
    """Tek bir coin'i paralel olarak işle (worker fonksiyonu)"""
    symbol, filename = args
    
    if not os.path.exists(filename):
        return symbol, []
    
    try:
        df = pd.read_csv(filename)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df[(df['timestamp'] >= BACKTEST_START) & (df['timestamp'] <= BACKTEST_END)]
        
        if len(df) < 50:
            return symbol, []
        
        df = calculate_indicators(df)
        trades = backtest_coin(symbol, df)
        return symbol, trades
    except Exception as e:
        return symbol, []

def run_monte_carlo_analysis(all_trades):
    """Monte Carlo Simülasyonu: İşlemlerin sırasını karıştırarak risk analizi yapar"""
    if not all_trades: return
    
    print("\n" + "=" * 70)
    print("🎲 MONTE CARLO ANALİZİ (5000 Simülasyon)")
    print("=" * 70)
    
    returns = [t['pnl_pct'] * LEVERAGE for t in all_trades]
    simulations = MONTE_CARLO_SIMULATIONS
    final_balances = []
    max_drawdowns = []
    ruined_count = 0
    
    for _ in range(simulations):
        # GERÇEKÇİ MONTE CARLO: Sadece karıştırma değil, Bootstrap Resampling (Yerine koyarak seçme)
        # Mevcut işlem listesinden rastgele işlemler seçerek yeni bir seri oluşturur.
        # Bu, kârlılık oranlarında varyasyon yaratır.
        shuffled_returns = random.choices(returns, k=len(returns))
        
        balance = INITIAL_BALANCE
        temp_drawdowns = []
        peak = INITIAL_BALANCE
        
        for pnl in shuffled_returns:
            pos_size = balance * (POSITION_SIZE_PCT / 100)
            profit = pos_size * (pnl / 100)
            fee = pos_size * LEVERAGE * (MAKER_FEE + TAKER_FEE)
            balance += profit - fee
            
            if balance <= 0:
                balance = 0
                ruined_count += 1
                break
                
            if balance > peak:
                peak = balance
            
            dd = (peak - balance) / peak * 100
            temp_drawdowns.append(dd)
            
        final_balances.append(balance)
        if temp_drawdowns:
            max_drawdowns.append(max(temp_drawdowns))
        else:
            max_drawdowns.append(100)

    # İstatistikler
    final_balances = np.array(final_balances)
    max_drawdowns = np.array(max_drawdowns)
    
    print(f"📈 Ortalama Final Bakiye: ${np.mean(final_balances):.2f}")
    print(f"🛡️ En Kötü Senaryo (Min): ${np.min(final_balances):.2f}")
    print(f"🚀 En İyi Senaryo (Max): ${np.max(final_balances):.2f}")
    print(f"📉 Ortalama Max Drawdown: %{np.mean(max_drawdowns):.2f}")
    print(f"💀 Maksimum Drawdown (En Kötü): %{np.max(max_drawdowns):.2f}")
    
    # Güven Aralıkları
    p5 = np.percentile(final_balances, 5)
    p50 = np.percentile(final_balances, 50)
    p95 = np.percentile(final_balances, 95)
    
    print("-" * 70)
    print(f"📊 %95 Güven Aralığı (En Az): ${p5:.2f}")
    print(f"📊 %50 Medyan (Beklenen): ${p50:.2f}")
    print(f"📊 %5 Üst Segment (Potansiyel): ${p95:.2f}")
    
    risk_of_ruin = (ruined_count / simulations) * 100
    print("-" * 70)
    print(f"🚨 İFLAS RİSKİ (Risk of Ruin): %{risk_of_ruin:.2f}")
    
    if risk_of_ruin < 1:
        print("✅ STRATEJİ SON DERECE SAĞLAM (İstatistiksel olarak güvenilir)")
    elif risk_of_ruin < 5:
        print("⚠️ STRATEJİ RİSKLİ (Pozisyon boyutunu küçültmeyi düşünün)")
    else:
        print("❌ STRATEJİ ÇOK TEHLİKELİ (Casinodan farkı yok!)")
    print("=" * 70)

# ==========================================
# 🚀 ANA BACKTEST
# ==========================================
def run_backtest():
    """CSV'lerden backtest çalıştır (PARALEL)"""
    num_workers = cpu_count()
    
    print("=" * 70)
    print("🚀 HIZLI BACKTEST (CSV'DEN) - PARALEL MOD")
    print("=" * 70)
    print(f"📅 Tarih Aralığı: {BACKTEST_START.strftime('%Y-%m-%d')} - {BACKTEST_END.strftime('%Y-%m-%d')}")
    print(f"💰 Başlangıç: ${INITIAL_BALANCE} | Kaldıraç: {LEVERAGE}x")
    print(f"⚡ CPU Çekirdek: {num_workers} (Paralel İşlem)")
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
    
    total_coins = len(coin_list)
    print(f"\n📋 {total_coins} coin yükleniyor ({num_workers} çekirdekte paralel)...\n")
    
    # Worker argümanlarını hazırla
    tasks = [(row['symbol'], row['file']) for _, row in coin_list.iterrows()]
    
    all_trades = []
    analyzed = 0
    
    # PARALEL İŞLEM
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(_process_coin, task): task[0] for task in tasks}
        
        for future in as_completed(futures):
            symbol = futures[future]
            analyzed += 1
            print(f"\r⚡ [{analyzed}/{total_coins}] {symbol} tamamlandı...", end="        ")
            
            try:
                sym, trades = future.result()
                if trades:
                    all_trades.extend(trades)
            except Exception as e:
                print(f"\n⚠️ {symbol} hata: {e}")
    
    print(f"\n\n✅ {analyzed} coin analiz edildi (Paralel)")

    
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

    # Monte Carlo Analizini Çalıştır
    if RUN_MONTE_CARLO:
        run_monte_carlo_analysis(all_trades)

    # 🔍 METRİK ANALİZİ
    print("\n" + "=" * 70)
    print("🔍 TEKNİK METRİK ANALİZİ (Hangi kriter zarara sokuyor?)")
    print("=" * 70)
    
    reason_stats = {}
    for t in all_trades:
        if 'reasons' not in t: continue
        is_loss = t['pnl_pct'] < 0
        for r in t['reasons']:
            # Puanı değil metrik adını al (örn: ADX+DI- (30) -> ADX+DI-)
            metric = r.split('(')[0] if '(' in r else r
            if metric not in reason_stats:
                reason_stats[metric] = {'total': 0, 'wins': 0, 'losses': 0, 'pnl': 0}
            
            reason_stats[metric]['total'] += 1
            if is_loss:
                reason_stats[metric]['losses'] += 1
            else:
                reason_stats[metric]['wins'] += 1
            reason_stats[metric]['pnl'] += t['pnl_pct']

    # Tabloyu yazdır
    print(f"{'Metrik':<20} | {'İşlem':<6} | {'Win Rate':<8} | {'Toplam PnL':<10}")
    print("-" * 55)
    for m, s in sorted(reason_stats.items(), key=lambda x: x[1]['pnl']):
        wr = (s['wins'] / s['total'] * 100) if s['total'] > 0 else 0
        print(f"{m:<20} | {s['total']:<6} | {wr:>7.1f}% | {s['pnl']:>+9.2f}%")

if __name__ == "__main__":
    import time
    start = time.time()
    run_backtest()
    print(f"\n⏱️ Süre: {time.time() - start:.1f} saniye")
