import pandas as pd
import numpy as np

df = pd.read_csv('backtest_positions.csv', sep=';', decimal=',')
print('=== TEMEL İSTATİSTİKLER ===')
print(f'Toplam Pozisyon: {len(df)}')
print(f'Baslangic Bakiye: $1000')

# Win/Loss/Neutral
wins = df[df['total_pnl_usd'] > 0]
losses = df[df['total_pnl_usd'] < 0]
neutral = df[df['total_pnl_usd'] == 0]
print(f'\nKazanc: {len(wins)} | Kayip: {len(losses)} | Notr: {len(neutral)}')
print(f'Win Rate: {len(wins)/len(df)*100:.1f}%')

# PnL Stats
print(f'\nToplam PnL USD: ${df["total_pnl_usd"].sum():.2f}')
print(f'Ort Kazanc: ${wins["total_pnl_usd"].mean():.2f}')
print(f'Ort Kayip: ${losses["total_pnl_usd"].mean():.2f}')
print(f'Medyan Kazanc: ${wins["total_pnl_usd"].median():.2f}')
print(f'Medyan Kayip: ${losses["total_pnl_usd"].median():.2f}')

max_win_idx = wins["total_pnl_usd"].idxmax()
max_loss_idx = losses["total_pnl_usd"].idxmin()
print(f'Max Kazanc: ${wins.loc[max_win_idx, "total_pnl_usd"]:.2f} ({wins.loc[max_win_idx, "symbol"]})')
print(f'Max Kayip: ${losses.loc[max_loss_idx, "total_pnl_usd"]:.2f} ({losses.loc[max_loss_idx, "symbol"]})')

# Risk/Reward
avg_win_pct = wins['total_pnl_pct'].mean()
avg_loss_pct = abs(losses['total_pnl_pct'].mean())
print(f'\nOrt Kazanc %: {avg_win_pct:.2f}%')
print(f'Ort Kayip %: -{avg_loss_pct:.2f}%')
print(f'Risk/Reward: 1:{avg_win_pct/avg_loss_pct:.2f}')

# Expectancy (beklenti)
wr = len(wins)/len(df)
expectancy = (wr * avg_win_pct) - ((1-wr) * avg_loss_pct)
print(f'Expectancy (Beklenti): {expectancy:.3f}%')

# Profit Factor
gross_profit = wins['total_pnl_usd'].sum()
gross_loss = abs(losses['total_pnl_usd'].sum())
print(f'Profit Factor: {gross_profit/gross_loss:.2f}')

# Consecutive wins/losses
results = (df['total_pnl_usd'] > 0).astype(int).values
max_consec_loss = 0
curr = 0
consec_losses = []
for r in results:
    if r == 0:
        curr += 1
        max_consec_loss = max(max_consec_loss, curr)
    else:
        if curr > 0: consec_losses.append(curr)
        curr = 0
if curr > 0: consec_losses.append(curr)
print(f'\nMax Ardisik Kayip: {max_consec_loss}')
if consec_losses:
    print(f'Ort Ardisik Kayip: {np.mean(consec_losses):.1f}')

# Drawdown analysis
balance = 1000
peak = 1000
drawdowns = []
balances = []
for _, row in df.iterrows():
    balance += row['total_pnl_usd']
    balances.append(balance)
    if balance > peak:
        peak = balance
    dd = (peak - balance) / peak * 100
    drawdowns.append(dd)
max_dd = max(drawdowns)
final_balance = balance
print(f'Max Drawdown: %{max_dd:.2f}')
print(f'Final Bakiye: ${final_balance:.2f}')
total_return = (final_balance - 1000) / 1000 * 100
print(f'Toplam Getiri: %{total_return:.2f}')

# Sharpe-like calculation
returns_arr = df['total_pnl_pct'].values
sharpe = np.mean(returns_arr) / np.std(returns_arr) if np.std(returns_arr) > 0 else 0
print(f'Sharpe Ratio (per-trade): {sharpe:.3f}')

# Calmar-like
calmar = total_return / max_dd if max_dd > 0 else 0
print(f'Calmar Ratio: {calmar:.2f}')

# Sortino (downside deviation)
downside = returns_arr[returns_arr < 0]
downside_std = np.std(downside) if len(downside) > 0 else 1
sortino = np.mean(returns_arr) / downside_std
print(f'Sortino Ratio (per-trade): {sortino:.3f}')

# Kelly Criterion
p = wr
q = 1 - p
b = avg_win_pct / avg_loss_pct  # average win / average loss ratio
kelly = (p * b - q) / b
print(f'Kelly Criterion: {kelly*100:.1f}%')
print(f'Half-Kelly (Onerilen): {kelly*50:.1f}%')

# Par cinsinden analiz
pnl_pct_arr = df['total_pnl_pct'].values * 7  # 7x leverage
print(f'\n=== KALDIRACLI METRIKLIAR (7x) ===')
print(f'Ort Kaldiracli Getiri/Pozisyon: {np.mean(pnl_pct_arr):.2f}%')
print(f'Std Kaldiracli Getiri: {np.std(pnl_pct_arr):.2f}%')
print(f'Skewness: {pd.Series(pnl_pct_arr).skew():.2f}')
print(f'Kurtosis: {pd.Series(pnl_pct_arr).kurtosis():.2f}')

# Coin bazli performans
print('\n=== EN IYI 10 COIN (Net PnL USD) ===')
coin_perf = df.groupby('symbol').agg(
    trade_count=('total_pnl_usd', 'count'),
    total_pnl=('total_pnl_usd', 'sum'),
    avg_pnl=('total_pnl_usd', 'mean'),
    win_rate=('total_pnl_usd', lambda x: (x > 0).sum() / len(x) * 100)
).sort_values('total_pnl', ascending=False)
print(coin_perf.head(10).to_string())
print('\n=== EN KOTU 10 COIN ===')
print(coin_perf.tail(10).to_string())

# Result type analysis
print('\n=== SONUC TIPI ANALIZI ===')
full_tp = df[df['results'].str.contains('TP3', na=False)]
partial_tp = df[df['results'].str.contains('TP1', na=False) & ~df['results'].str.contains('TP3', na=False)]
sl_only = df[df['results'].str.contains('STOP LOSS', na=False) & ~df['results'].str.contains('TP', na=False)]
trailing = df[df['results'].str.contains('TRAILING', na=False)]
donem = df[df['results'].str.contains('DÖNEM SONU', na=False) & ~df['results'].str.contains('TP', na=False)]
print(f'Full TP (TP3 hedefine ulasan): {len(full_tp)} ({len(full_tp)/len(df)*100:.1f}%)')
print(f'Partial TP (TP1/TP2 + Trailing): {len(partial_tp)} ({len(partial_tp)/len(df)*100:.1f}%)')
print(f'Pure Stop Loss: {len(sl_only)} ({len(sl_only)/len(df)*100:.1f}%)')
print(f'Trailing Stop: {len(trailing)} ({len(trailing)/len(df)*100:.1f}%)')
print(f'Donem Sonu (acik): {len(donem)} ({len(donem)/len(df)*100:.1f}%)')

# TP3 orani
print(f'\nFull TP ort PnL: ${full_tp["total_pnl_usd"].mean():.2f}')
print(f'Partial TP ort PnL: ${partial_tp["total_pnl_usd"].mean():.2f}')
print(f'Stop Loss ort PnL: ${sl_only["total_pnl_usd"].mean():.2f}')

# Average holding time
df['entry_time'] = pd.to_datetime(df['entry_time'])
df['exit_time'] = pd.to_datetime(df['exit_time'])
df['hold_hours'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600
print(f'\nOrt Pozisyon Suresi: {df["hold_hours"].mean():.1f} saat')
print(f'Kazanc Ort Sure: {df.loc[df["total_pnl_usd"]>0, "hold_hours"].mean():.1f} saat')
print(f'Kayip Ort Sure: {df.loc[df["total_pnl_usd"]<0, "hold_hours"].mean():.1f} saat')

# Time analysis 
df['hour'] = df['entry_time'].dt.hour
hour_perf = df.groupby('hour')['total_pnl_usd'].agg(['sum','count','mean']).sort_values('sum')
print('\n=== SAAT BAZLI GIRIS PERFORMANSI (en kotuden en iyiye) ===')
print(hour_perf.to_string())

# Day of week
df['dow'] = df['entry_time'].dt.day_name()
dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
dow_perf = df.groupby('dow')['total_pnl_usd'].agg(['sum','count','mean']).reindex(dow_order)
print('\n=== GUN BAZLI PERFORMANS ===')
print(dow_perf.to_string())

# Correlation: Balance vs Position Size Improvement
# Birikimli kazanc vs islem buyuklugu
print('\n=== MARJIN EROZYON ANALIZI ===')
early = df.head(100)
late = df.tail(100)
print(f'Ilk 100 pozisyon: Win Rate: {(early["total_pnl_usd"]>0).sum()}%, Ort PnL: ${early["total_pnl_usd"].mean():.2f}')
print(f'Son 100 pozisyon: Win Rate: {(late["total_pnl_usd"]>0).sum()}%, Ort PnL: ${late["total_pnl_usd"].mean():.2f}')

# Eşzamanlı açık pozisyon sayısı
print('\n=== ES ZAMANLI ACIK POZISYON ANALIZI ===')
events = []
for _, row in df.iterrows():
    events.append((row['entry_time'], 1))
    events.append((row['exit_time'], -1))
events.sort()
max_concurrent = 0
curr_concurrent = 0
for _, delta in events:
    curr_concurrent += delta
    max_concurrent = max(max_concurrent, curr_concurrent)
print(f'Max eslesen acik pozisyon: {max_concurrent}')
print(f'Ort eslesen: hesaplaniyor...')

# Bunun uzerinden marjin riski
max_exposure_pct = max_concurrent * 10  # her biri %10 margin
print(f'Tepe Noktasi Toplam Marjin Kullanimi: %{max_exposure_pct}')
print(f'Tepe Noktasi Gercek Pozisyon: %{max_exposure_pct * 7} (7x kaldiracli)')
