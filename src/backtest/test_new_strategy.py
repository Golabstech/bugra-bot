import pandas as pd
import pandas_ta as ta
import os
import numpy as np
import asyncio
from datetime import datetime

# --- MATHEMATICAL SNIPER (Fixed R:R) ---
DATA_DIR = r'c:\Users\murat\bugra-bot\backtest_data'
INITIAL_BALANCE = 1000
LEVERAGE = 5
MAX_CONCURRENT_TRADES = 4
COMMISSION_RATE = 0.0002 # Maker Fee
SLIPPAGE = 0.0000 # Limit Emir = 0 Kayma
RISK_PER_TRADE = 0.02

class BacktestStrategy:
    def __init__(self, params=None):
        defaults = {
            'bb_length': 20,
            'bb_std': 2.0,        
            'vwap_filter': True,  # Trend Takip (Daha Yüksek Başarı)
            'rsi_length': 14,
            'rsi_os': 30,         # Sıkı Aşırı Satım
            'rsi_ob': 70,         # Sıkı Aşırı Alım
            'time_exit_bars': 24  # 6 Saat (Swing fırsatı)
        }
        self.params = {**defaults, **(params or {})}

    def generate_signal_numpy(self, row_data, prev_row):
        c, l, h = row_data['close'], row_data['low'], row_data['high']
        prev_l, prev_h = prev_row['low'], prev_row['high']
        vwap = row_data['vwap']
        bbu, bbm, bbl = row_data['BBU_20_2.0'], row_data['BBM_20_2.0'], row_data['BBL_20_2.0']
        prev_bbl, prev_bbu = prev_row['BBL_20_2.0'], prev_row['BBU_20_2.0']
        rsi = row_data['rsi']
        atr = row_data['atr']
        
        # 🚀 LONG
        is_uptrend = (c > vwap) if self.params.get('vwap_filter', True) else True
        if is_uptrend:
            if prev_l < prev_bbl and c > bbl and rsi < self.params['rsi_os']:
                swing_low_sl = min(prev_l, l) * 0.995 
                max_sl = c * 0.98 # Max %2 Zarar Limiti
                sl = max(swing_low_sl, max_sl) 
                
                tp = bbm # Dynamic Target
                
                risk = c - sl
                reward = tp - c
                if risk > 0 and (reward / risk) >= 1.0: # En az 1:1 R:R
                    return {'side': 'LONG', 'entry': c, 'sl': sl, 'tp': tp, 'setup': 'SMART_LONG'}

        # 🔻 SHORT
        is_downtrend = (c < vwap) if self.params.get('vwap_filter', True) else True
        if is_downtrend:
            if prev_h > prev_bbu and c < bbu and rsi > self.params['rsi_ob']:
                swing_high_sl = max(prev_h, h) * 1.005
                max_sl = c * 1.02 # Max %2 Zarar
                sl = min(swing_high_sl, max_sl) # Hangisi daha yakındaysa
                
                tp = bbm
                
                risk = sl - c
                reward = c - tp
                if risk > 0 and (reward / risk) >= 1.0:
                    return {'side': 'SHORT', 'entry': c, 'sl': sl, 'tp': tp, 'setup': 'SMART_SHORT'}

        return None

def pre_calculate_data(filepath):
    try:
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        for c in ['open','high','low','close','volume']: df[c] = df[c].astype(float)
        
        if len(df) < 200: return None
        
        df.ta.vwap(append=True)
        if 'VWAP_D' in df.columns: df.rename(columns={'VWAP_D': 'vwap'}, inplace=True)
        else: df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
        
        bb = df.ta.bbands(length=20, std=2.0)
        df = pd.concat([df, bb], axis=1)
        
        # Kolon İsimlerini Otomatik Bul
        bbl_col = bb.columns[0]
        bbm_col = bb.columns[1]
        bbu_col = bb.columns[2]
        
        df['rsi'] = ta.rsi(df['close'], length=14)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14) # ATR Eklendi
        
        df.dropna(inplace=True)
        
        cols = ['open','high','low','close','vwap', bbu_col, bbm_col, bbl_col, 'rsi', 'atr']
        
        data_arrays = {col: df[col].values for col in ['open','high','low','close','vwap','rsi','atr']}
        data_arrays['BBU_20_2.0'] = df[bbu_col].values
        data_arrays['BBM_20_2.0'] = df[bbm_col].values
        data_arrays['BBL_20_2.0'] = df[bbl_col].values
        data_arrays['timestamp'] = df.index.values
        return data_arrays
    except: return None

def simulate_portfolio(all_signals):
    balance = INITIAL_BALANCE
    max_balance = INITIAL_BALANCE
    max_dd = 0
    active = []
    history = []
    
    all_signals.sort(key=lambda x: x['entry_time'])
    
    for sig in all_signals:
        now = sig['entry_time']
        for t in active[:]:
            if t['exit_time'] <= now:
                pnl = (t['size'] * t['pnl_pct'] / 100) - (t['size'] * COMMISSION_RATE * 2)
                balance += (t['margin'] + pnl)
                max_balance = max(max_balance, balance)
                if max_balance > 0: max_dd = max(max_dd, (max_balance - balance) / max_balance * 100)
                history.append(pnl)
                active.remove(t)
        
        if len(active) < MAX_CONCURRENT_TRADES and balance > 100:
            if any(a['symbol'] == sig['symbol'] for a in active): continue
            
            risk_amt = balance * RISK_PER_TRADE
            dist_pct = abs(sig['entry'] - sig['sl']) / sig['entry']
            if dist_pct < 0.005: dist_pct = 0.005
            
            # Position Sizing
            pos_size = min(risk_amt / dist_pct, balance * LEVERAGE * 0.95)
            margin = pos_size / LEVERAGE
            
            if margin <= balance:
                balance -= margin
                active.append({**sig, 'size': pos_size, 'margin': margin})

    return balance, max_dd, history

async def fast_backtest(params, preloaded):
    strategy = BacktestStrategy(params)
    signals = []
    
    for symbol, data in preloaded:
        times, closes, highs, lows = data['timestamp'], data['close'], data['high'], data['low']
        num = len(closes)
        
        for i in range(200, num - 50):
            row = {
                'close': closes[i], 'low': lows[i], 'high': highs[i],
                'vwap': data['vwap'][i], 'rsi': data['rsi'][i], 'atr': data['atr'][i],
                'BBU_20_2.0': data['BBU_20_2.0'][i],
                'BBM_20_2.0': data['BBM_20_2.0'][i], 
                'BBL_20_2.0': data['BBL_20_2.0'][i]
            }
            prev_row = {
                'low': lows[i-1], 'high': highs[i-1],
                'BBU_20_2.0': data['BBU_20_2.0'][i-1],
                'BBL_20_2.0': data['BBL_20_2.0'][i-1]
            }
            
            res = strategy.generate_signal_numpy(row, prev_row)
            
            if res:
                entry = res['entry'] * (1+SLIPPAGE if res['side']=='LONG' else 1-SLIPPAGE)
                tp, sl = res['tp'], res['sl']
                pnl, exit_t = 0, times[i+12] # Default exit time
                
                # Math Exit Loop
                exit_reason = 'TIME_EXIT' # Varsayılan
                for j in range(i+1, min(i+100, num)): # 100 mum (1 gün) bekle
                    c_h, c_l = highs[j], lows[j]
                    
                    if res['side'] == 'LONG':
                        if c_l <= sl: 
                            pnl=(sl-entry)/entry*100; exit_t=times[j]; exit_reason='STOP_LOSS'
                            break
                        if c_h >= tp: 
                            pnl=(tp-entry)/entry*100; exit_t=times[j]; exit_reason='TAKE_PROFIT'
                            break
                    else:
                        if c_h >= sl: 
                            pnl=(entry-sl)/entry*100; exit_t=times[j]; exit_reason='STOP_LOSS'
                            break
                        if c_l <= tp: 
                            pnl=(entry-tp)/entry*100; exit_t=times[j]; exit_reason='TAKE_PROFIT'
                            break
                        
                signals.append({**res, 'symbol': symbol, 'entry_time': pd.Timestamp(times[i]), 'exit_time': pd.Timestamp(exit_t), 'pnl_pct': pnl, 'exit_reason': exit_reason})
                
    return simulate_portfolio(signals)

if __name__ == "__main__":
    import time
    start_t = time.time()
    print("🚀 ELASTIC REVERSION ENGINE STARTING...")
    
    # 1. Veri Hazırlığı
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv') and not f.startswith('_')]
    print(f"📊 {len(files)} Sembol taranıyor...")
    
    preloaded_data = []
    for f in files:
        d = pre_calculate_data(os.path.join(DATA_DIR, f))
        if d: preloaded_data.append((f.replace('.csv',''), d))
            
    print(f"✅ Hazır Veri: {len(preloaded_data)} adet. ({time.time()-start_t:.2f}s)")
    
    # 2. Backtest Koşusu
    # Default parametreleri kullan (RSI 30/70, VWAP True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        balance, dd, history = loop.run_until_complete(fast_backtest({}, preloaded_data))
        
        # 3. Rapor
        total_profit = balance - INITIAL_BALANCE
        roi = str(round((total_profit/INITIAL_BALANCE)*100, 2))
        win_rate = len([x for x in history if x > 0]) / len(history) * 100 if history else 0
        
        print("\n" + "="*40)
        print(f"🏆 BACKTEST SONUCU (15m Elastic Sniper)")
        print("="*40)
        print(f"💰 Net Bakiye:   ${balance:.2f} ({roi}%)")
        print(f"📉 Max Drawdown: %{dd:.2f}")
        print(f"📊 Toplam İşlem: {len(history)}")
        print(f"🎯 Win Rate:     %{win_rate:.2f}")
        print("="*40)
        
    finally:
        loop.close()
