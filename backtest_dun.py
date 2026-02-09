import ccxt
import pandas as pd
import pandas_ta as ta
import warnings
import time
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')
pd.set_option('future.no_silent_downcasting', True)

# ==========================================
# ⚙️ BACKTEST AYARLARI
# ==========================================
INITIAL_BALANCE = 1000  # Başlangıç bakiyesi $
POSITION_SIZE_PCT = 10  # Her işlem için bakiyenin %10'u
LEVERAGE = 10           # Kaldıraç
MAKER_FEE = 0.0002      # %0.02
TAKER_FEE = 0.0005      # %0.05

# Tarama aralığı
START_RANK = 50
END_RANK = 100

# 📅 TARİH ARALIĞI (1-8 Şubat 2026)
BACKTEST_START = datetime(2026, 2, 1, 0, 0, 0)
BACKTEST_END = datetime(2026, 2, 8, 23, 59, 59)

# ⚡ GELİŞTİRİLMİŞ FİLTRELER v3
SCORE_THRESHOLD = 80        # 70'den 80'e - daha seçici
MIN_WIN_RATE = 75           # 70'den 75'e
COOLDOWN_CANDLES = 8        # Stop sonrası 8 mum bekle (2 saat)
MAX_DAILY_TRADES_PER_COIN = 10  # Haftalık backtest için artırıldı
USE_MULTI_TF = True         # Multi-timeframe onay
PARTIAL_TP = True           # Kısmi TP al
TRAILING_STOP = True        # Trailing stop aktif

# 🎯 YENİ: VOLATİLİTE FİLTRESİ
MAX_ATR_PERCENT = 5.0       # ATR/Price > %5 olan coinleri atla (çok volatil)
MIN_ATR_PERCENT = 0.5       # ATR/Price < %0.5 olan coinleri atla (çok durgun)

# 🎯 YENİ: PARTIAL TP ORANLARI (daha agresif tutma)
TP1_CLOSE_PCT = 0.30        # TP1'de %30 kapat (eskisi %50)
TP2_CLOSE_PCT = 0.30        # TP2'de %30 kapat
TP3_CLOSE_PCT = 0.40        # TP3'te kalan %40 kapat

# 🎯 YENİ: GENİŞLETİLMİŞ SL VE TP
SL_ATR_MULT = 2.5           # Stop Loss = ATR * 2.5 (eskisi 2.0)
TP1_RR = 1.5                # TP1 Risk/Reward 1:1.5 (eskisi 1:1)
TP2_RR = 2.5                # TP2 Risk/Reward 1:2.5
TP3_RR = 4.0                # TP3 Risk/Reward 1:4

# ==========================================
# 🔌 BORSA BAĞLANTISI
# ==========================================
exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})

def get_sorted_coins():
    """Hacme göre sıralı coinleri al"""
    try:
        markets = exchange.load_markets()
        tickers = exchange.fetch_tickers()
        
        futures = []
        for symbol, ticker in tickers.items():
            if '/USDT:USDT' in symbol and ticker.get('quoteVolume'):
                futures.append({
                    'symbol': symbol, 
                    'volume': float(ticker.get('quoteVolume', 0))
                })
        
        futures.sort(key=lambda x: x['volume'], reverse=True)
        return futures[START_RANK-1:END_RANK]
    except Exception as e:
        print(f"Coin listesi alınamadı: {e}")
        return []

def fetch_historical_ohlcv(symbol, tf='15m', days=10):
    """Belirli gün sayısı kadar geçmiş veri çek - retry mekanizmalı"""
    for attempt in range(3):
        try:
            # Binance max 1500 mum
            if tf == '15m':
                limit = min(days * 24 * 4, 1500)  # 15dk = günde 96 mum
            elif tf == '1h':
                limit = min(days * 24, 1000)
            else:
                limit = min(days, 500)
            
            # Backtest başlangıç tarihinden itibaren çek
            since = int(BACKTEST_START.timestamp() * 1000)
            
            data = exchange.fetch_ohlcv(symbol, tf, since=since, limit=limit)
            return data
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
            continue
    return None

def calculate_indicators(df):
    """İndikatörleri hesapla"""
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

def check_1h_trend(symbol):
    """1 saatlik trend kontrolü - SHORT için düşüş trendi olmalı"""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '1h', limit=50)
        if not ohlcv or len(ohlcv) < 30:
            return False, 0
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['ema9'] = ta.ema(df['close'], length=9)
        df['ema21'] = ta.ema(df['close'], length=21)
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        last = df.iloc[-1]
        ema9 = float(last['ema9']) if pd.notna(last['ema9']) else 0
        ema21 = float(last['ema21']) if pd.notna(last['ema21']) else 0
        rsi = float(last['rsi']) if pd.notna(last['rsi']) else 50
        
        # Düşüş trendi kontrolü
        bearish_score = 0
        if ema9 < ema21:
            bearish_score += 30
        if rsi > 55:  # Overbought bölgesine yakın
            bearish_score += 20
        
        return bearish_score >= 30, bearish_score
    except:
        return True, 50  # Hata durumunda geç

def backtest_coin(symbol, df, df_1h=None):
    """Tek coin için geliştirilmiş backtest v3"""
    trades = []
    in_position = False
    entry_price = 0
    entry_time = None
    stop_loss = 0
    original_stop = 0
    tp1 = tp2 = tp3 = 0
    tp1_hit = tp2_hit = False
    
    # Pozisyon boyutları (kısmi TP için)
    position_remaining = 1.0  # %100
    
    # Cooldown ve limit takibi
    last_exit_candle = -999
    daily_trades = 0
    
    # Volatilite kontrolü için ilk ATR hesapla
    first_atr = df.iloc[50]['atr'] if len(df) > 50 and pd.notna(df.iloc[50]['atr']) else 0
    first_price = df.iloc[50]['close'] if len(df) > 50 else 1
    atr_pct = (first_atr / first_price) * 100 if first_price > 0 else 0
    
    # Volatilite filtresi
    if atr_pct > MAX_ATR_PERCENT:
        return []  # Çok volatil, atla
    if atr_pct < MIN_ATR_PERCENT:
        return []  # Çok durgun, atla
    
    for i in range(50, len(df)):  # İlk 50 mum warmup
        row = df.iloc[i]
        current_price = float(row['close'])
        current_time = row['timestamp']
        high = float(row['high'])
        low = float(row['low'])
        atr = float(row['atr']) if pd.notna(row['atr']) else current_price * 0.02
        
        if in_position:
            # ===== TRAILING STOP (GEVŞETİLMİŞ) =====
            if TRAILING_STOP:
                # TP1'e ulaştıktan sonra stop'u %50 yaklaştır (break-even değil)
                if tp1_hit and not tp2_hit:
                    new_stop = entry_price + (original_stop - entry_price) * 0.5
                    if stop_loss > new_stop:
                        stop_loss = new_stop
                
                # TP2'ye ulaştıktan sonra stop'u entry'ye çek
                if tp2_hit:
                    if stop_loss > entry_price:
                        stop_loss = entry_price
            
            # ===== STOP LOSS KONTROL =====
            if high >= stop_loss:
                # Kalan pozisyon için PNL hesapla
                pnl_pct = ((entry_price - stop_loss) / entry_price) * 100 * position_remaining
                
                result_text = 'STOP LOSS'
                if tp1_hit:
                    result_text = 'TRAILING STOP (TP1+)'
                if tp2_hit:
                    result_text = 'TRAILING STOP (TP2+)'
                
                trades.append({
                    'symbol': symbol,
                    'entry_time': entry_time,
                    'exit_time': current_time,
                    'entry_price': entry_price,
                    'exit_price': stop_loss,
                    'pnl_pct': pnl_pct,
                    'result': result_text
                })
                in_position = False
                last_exit_candle = i
                position_remaining = 1.0
                continue
            
            # ===== PARTIAL TP KONTROL (YENİ ORANLAR) =====
            if PARTIAL_TP:
                # TP1: Pozisyonun %30'unu kapat
                if not tp1_hit and low <= tp1:
                    tp1_hit = True
                    partial_pnl = ((entry_price - tp1) / entry_price) * 100 * TP1_CLOSE_PCT
                    trades.append({
                        'symbol': symbol,
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': tp1,
                        'pnl_pct': partial_pnl,
                        'result': f'TP1 ({int(TP1_CLOSE_PCT*100)}%)'
                    })
                    position_remaining = 1.0 - TP1_CLOSE_PCT
                
                # TP2: %30 kapat
                if tp1_hit and not tp2_hit and low <= tp2:
                    tp2_hit = True
                    partial_pnl = ((entry_price - tp2) / entry_price) * 100 * TP2_CLOSE_PCT
                    trades.append({
                        'symbol': symbol,
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': tp2,
                        'pnl_pct': partial_pnl,
                        'result': f'TP2 ({int(TP2_CLOSE_PCT*100)}%)'
                    })
                    position_remaining = TP3_CLOSE_PCT
                
                # TP3: Kalan %40'ı kapat
                if tp2_hit and low <= tp3:
                    partial_pnl = ((entry_price - tp3) / entry_price) * 100 * TP3_CLOSE_PCT
                    trades.append({
                        'symbol': symbol,
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': tp3,
                        'pnl_pct': partial_pnl,
                        'result': f'TP3 ({int(TP3_CLOSE_PCT*100)}%)'
                    })
                    in_position = False
                    last_exit_candle = i
                    position_remaining = 1.0
                    continue
            else:
                # Partial TP kapalıysa eski mantık
                if not tp1_hit and low <= tp1:
                    tp1_hit = True
                if not tp2_hit and low <= tp2:
                    tp2_hit = True
                if low <= tp3:
                    pnl_pct = ((entry_price - tp3) / entry_price) * 100
                    trades.append({
                        'symbol': symbol,
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': tp3,
                        'pnl_pct': pnl_pct,
                        'result': 'TP3'
                    })
                    in_position = False
                    last_exit_candle = i
                    continue
        
        else:
            # ===== COOLDOWN KONTROLÜ =====
            if i - last_exit_candle < COOLDOWN_CANDLES:
                continue
            
            # ===== GÜNLÜK İŞLEM LİMİTİ =====
            if daily_trades >= MAX_DAILY_TRADES_PER_COIN:
                continue
            
            # ===== YENİ SİNYAL ARA =====
            score, reasons = calculate_short_score(row)
            
            # Win rate hesapla (geliştirilmiş)
            win_rate = 50
            if score >= 100: win_rate += 20
            elif score >= 80: win_rate += 15
            elif score >= 70: win_rate += 10
            elif score >= 60: win_rate += 5
            
            # Confluence bonus
            if len(reasons) >= 5:
                win_rate += 10
            elif len(reasons) >= 4:
                win_rate += 5
            
            if score >= SCORE_THRESHOLD and win_rate >= MIN_WIN_RATE:
                in_position = True
                entry_price = current_price
                entry_time = current_time
                daily_trades += 1
                
                # SL ve TP hesapla (YENİ ÇARPANLAR)
                risk = atr * SL_ATR_MULT
                original_stop = entry_price + risk
                stop_loss = original_stop
                tp1 = entry_price - (risk * TP1_RR)   # Risk/Reward 1:1.5
                tp2 = entry_price - (risk * TP2_RR)   # Risk/Reward 1:2.5
                tp3 = entry_price - (risk * TP3_RR)   # Risk/Reward 1:4
                tp1_hit = tp2_hit = False
                position_remaining = 1.0
    
    # Açık pozisyon kaldıysa son fiyattan kapat
    if in_position:
        last_row = df.iloc[-1]
        exit_price = float(last_row['close'])
        pnl_pct = ((entry_price - exit_price) / entry_price) * 100 * position_remaining
        trades.append({
            'symbol': symbol,
            'entry_time': entry_time,
            'exit_time': last_row['timestamp'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_pct': pnl_pct,
            'result': 'AÇIK (GÜN SONU)'
        })
    
    return trades

def run_backtest():
    """Ana backtest fonksiyonu"""
    print("=" * 70)
    print("🔄 HAFTALIK BACKTEST - SHORT STRATEJİSİ v3.0")
    print("=" * 70)
    print(f"📅 Tarih Aralığı: {BACKTEST_START.strftime('%Y-%m-%d')} - {BACKTEST_END.strftime('%Y-%m-%d')}")
    print(f"💰 Başlangıç Bakiye: ${INITIAL_BALANCE}")
    print(f"📊 Pozisyon: %{POSITION_SIZE_PCT} | Kaldıraç: {LEVERAGE}x")
    print(f"🎯 Tarama: {START_RANK}-{END_RANK} arası coinler")
    print("-" * 70)
    print("⚙️ STRATEJİ PARAMETRELERİ:")
    print(f"   Score: {SCORE_THRESHOLD} | Min Win Rate: {MIN_WIN_RATE}%")
    print(f"   Cooldown: {COOLDOWN_CANDLES} mum | Max İşlem/Coin: {MAX_DAILY_TRADES_PER_COIN}")
    print(f"   Volatilite Filtresi: %{MIN_ATR_PERCENT} - %{MAX_ATR_PERCENT}")
    print("-" * 70)
    print("🎯 RISK YÖNETİMİ:")
    print(f"   Stop Loss: ATR x {SL_ATR_MULT}")
    print(f"   TP1: 1:{TP1_RR} (%{int(TP1_CLOSE_PCT*100)} kapat)")
    print(f"   TP2: 1:{TP2_RR} (%{int(TP2_CLOSE_PCT*100)} kapat)")
    print(f"   TP3: 1:{TP3_RR} (%{int(TP3_CLOSE_PCT*100)} kapat)")
    print("=" * 70)
    
    # Coinleri al
    print("\n📋 Coin listesi alınıyor...")
    coins = get_sorted_coins()
    
    if not coins:
        print("❌ Coin listesi alınamadı!")
        return
    
    print(f"✅ {len(coins)} coin bulundu\n")
    
    all_trades = []
    analyzed = 0
    
    for i, coin in enumerate(coins, 1):
        symbol = coin['symbol']
        vol_m = coin['volume'] / 1_000_000
        
        sys.stdout.write(f"\r[{i}/{len(coins)}] {symbol} analiz ediliyor...        ")
        sys.stdout.flush()
        
        try:
            # Backtest döneminin verisini çek (15 dakikalık)
            ohlcv = fetch_historical_ohlcv(symbol, '15m', days=10)
            
            if not ohlcv or len(ohlcv) < 60:
                continue
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Backtest tarih aralığını filtrele
            df = df[(df['timestamp'] >= BACKTEST_START) & (df['timestamp'] <= BACKTEST_END)]
            
            if len(df) < 30:
                continue
            
            # İndikatörleri hesapla
            df = calculate_indicators(df)
            
            # Backtest
            trades = backtest_coin(symbol, df)
            
            if trades:
                all_trades.extend(trades)
            
            analyzed += 1
            time.sleep(0.2)
            
        except Exception as e:
            continue
    
    print(f"\n\n✅ {analyzed} coin analiz edildi")
    
    # Sonuçları hesapla
    if not all_trades:
        print("\n❌ Hiç işlem sinyali bulunamadı!")
        return
    
    print("\n" + "=" * 70)
    print("📊 İŞLEM DETAYLARI")
    print("=" * 70)
    
    # İstatistikler için sayaçlar
    tp1_count = tp2_count = tp3_count = sl_count = trailing_count = open_count = 0
    
    for trade in all_trades:
        pnl = trade['pnl_pct']
        result = trade['result']
        
        if pnl > 0:
            status = "✅"
        elif pnl < 0:
            status = "❌"
        else:
            status = "➖"
        
        # Sonuç sayaçları
        if 'TP1' in result: tp1_count += 1
        elif 'TP2' in result: tp2_count += 1
        elif 'TP3' in result: tp3_count += 1
        elif 'TRAILING' in result: trailing_count += 1
        elif 'STOP LOSS' in result: sl_count += 1
        elif 'AÇIK' in result: open_count += 1
        
        # Kaldıraçlı PNL
        leveraged_pnl = pnl * LEVERAGE
        position_size = INITIAL_BALANCE * (POSITION_SIZE_PCT / 100)
        usd_pnl = position_size * (leveraged_pnl / 100)
        
        print(f"\n{status} {trade['symbol']}")
        print(f"   Giriş: {trade['entry_time'].strftime('%H:%M')} @ ${trade['entry_price']:.6f}")
        print(f"   Çıkış: {trade['exit_time'].strftime('%H:%M')} @ ${trade['exit_price']:.6f}")
        print(f"   Sonuç: {trade['result']} | PNL: {pnl:.2f}% ({leveraged_pnl:.2f}% kaldıraçlı) | ${usd_pnl:+.2f}")
    
    # Kar/zarar ayrımı
    wins = [t for t in all_trades if t['pnl_pct'] > 0]
    losses = [t for t in all_trades if t['pnl_pct'] < 0]
    neutral = [t for t in all_trades if t['pnl_pct'] == 0]
    
    total_trades = len(all_trades)
    win_rate = (len(wins) / total_trades * 100) if total_trades > 0 else 0
    
    # Final bakiye hesapla
    final_balance = INITIAL_BALANCE
    for trade in all_trades:
        pnl = trade['pnl_pct'] * LEVERAGE
        position_size = final_balance * (POSITION_SIZE_PCT / 100)
        profit = position_size * (pnl / 100)
        fee = position_size * LEVERAGE * (MAKER_FEE + TAKER_FEE)
        final_balance += profit - fee
    
    profit_loss = final_balance - INITIAL_BALANCE
    
    # Detaylı özet
    print("\n" + "=" * 70)
    print("📊 DETAYLI İSTATİSTİKLER")
    print("=" * 70)
    print(f"🎯 Sonuç Dağılımı:")
    print(f"   TP1: {tp1_count} | TP2: {tp2_count} | TP3: {tp3_count}")
    print(f"   Trailing Stop: {trailing_count} | Stop Loss: {sl_count}")
    print(f"   Gün Sonu Açık: {open_count}")
    print("-" * 70)
    
    if wins:
        avg_win = sum(t['pnl_pct'] for t in wins) / len(wins)
        max_win = max(t['pnl_pct'] for t in wins)
        print(f"✅ Kazançlı İşlemler: {len(wins)}")
        print(f"   Ort. Kazanç: {avg_win:.2f}% | Max: {max_win:.2f}%")
    
    if losses:
        avg_loss = sum(t['pnl_pct'] for t in losses) / len(losses)
        max_loss = min(t['pnl_pct'] for t in losses)
        print(f"❌ Kayıplı İşlemler: {len(losses)}")
        print(f"   Ort. Kayıp: {avg_loss:.2f}% | Max: {max_loss:.2f}%")
    
    # Risk/Reward oranı
    if wins and losses:
        rr_ratio = abs(avg_win / avg_loss)
        print(f"📈 Risk/Reward: 1:{rr_ratio:.2f}")
    
    print("\n" + "=" * 70)
    print("💰 BACKTEST SONUCU")
    print("=" * 70)
    print(f"📈 Toplam İşlem: {total_trades}")
    print(f"✅ Kazanan: {len(wins)} | ❌ Kaybeden: {len(losses)} | ➖ Nötr: {len(neutral)}")
    print(f"📊 Win Rate: {win_rate:.1f}%")
    print(f"💵 Başlangıç: ${INITIAL_BALANCE:.2f}")
    print(f"💵 Final: ${final_balance:.2f}")
    print(f"{'📈' if profit_loss >= 0 else '📉'} Kar/Zarar: ${profit_loss:+.2f} ({profit_loss/INITIAL_BALANCE*100:+.2f}%)")
    print("=" * 70)

# İmport kontrolü
import sys

if __name__ == "__main__":
    run_backtest()
