import pandas as pd

df = pd.read_csv('backtest_positions.csv', sep=';', decimal=',')
trades = pd.read_csv('backtest_trades.csv', sep=';', decimal=',')
print(f'Toplam Pozisyon: {len(df)}')
print(f'Toplam Trade: {len(trades)}')

wins = df[df['total_pnl_usd'] > 0]
losses = df[df['total_pnl_usd'] < 0]
print(f'Win Rate: {len(wins)/len(df)*100:.1f}%')
print(f'Ort Kazanc: ${wins["total_pnl_usd"].mean():.2f}')
print(f'Ort Kayip: ${losses["total_pnl_usd"].mean():.2f}')
pf = wins['total_pnl_usd'].sum() / abs(losses['total_pnl_usd'].sum())
print(f'Profit Factor: {pf:.2f}')

# Eszmanlı pozisyon kontrolü
df['entry_time'] = pd.to_datetime(df['entry_time'])
df['exit_time'] = pd.to_datetime(df['exit_time'])
events = []
for _, row in df.iterrows():
    events.append((row['entry_time'], 1))
    events.append((row['exit_time'], -1))
events.sort()
max_c = 0
curr = 0
for _, d in events:
    curr += d
    max_c = max(max_c, curr)
print(f'Max Eszamanli: {max_c}')

# Drawdown
balance = 1000
peak = 1000
max_dd = 0
min_bal = 1000
for _, row in df.iterrows():
    balance += row['total_pnl_usd']
    if balance < min_bal: min_bal = balance
    if balance > peak: peak = balance
    dd = (peak - balance) / peak * 100
    if dd > max_dd: max_dd = dd
print(f'Final Bakiye: ${balance:.2f}')
print(f'Getiri: %{(balance-1000)/10:.1f}')
print(f'Max DD (peak-to-trough): %{max_dd:.1f}')
print(f'Min Bakiye: ${min_bal:.2f}')
