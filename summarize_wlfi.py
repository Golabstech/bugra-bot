import pandas as pd

df = pd.read_csv('backtest_trades.csv')
wlfi = df[df['symbol'].str.contains('WLFI', na=False)].copy()

print(f"Toplam Satır: {len(wlfi)}")

# Birleştirilmiş mantıklı işlem sayısı (Aynı entry_time olanları tek işlem sayalım)
logical_trades = wlfi.groupby(['entry_time']).size().reset_index()
print(f"Toplam Mantıksal İşlem: {len(logical_trades)}")

# Detayları yazdır
for entry_time in logical_trades['entry_time']:
    trade_group = wlfi[wlfi['entry_time'] == entry_time]
    print(f"\n--- İşlem Tarihi: {entry_time} ---")
    for _, row in trade_group.iterrows():
        print(f"  {row['result']}: {row['entry_price']} -> {row['exit_price']} | PnL%: {row['pnl_pct']:.2f}% | USD: {row['pnl_usd']:.2f}")
