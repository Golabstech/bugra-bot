import pandas as pd
import numpy as np

df = pd.read_csv('backtest_positions.csv', sep=';', decimal=',')

# Bakiye eğrisini yeniden oluştur
balance = 1000
peak = 1000
balances = []
peaks = []
drawdowns = []

for _, row in df.iterrows():
    balance += row['total_pnl_usd']
    balances.append(balance)
    if balance > peak:
        peak = balance
    peaks.append(peak)
    dd = (peak - balance) / peak * 100
    drawdowns.append(dd)

df['cumulative_balance'] = balances
df['peak_balance'] = peaks
df['drawdown_pct'] = drawdowns

# Max drawdown noktasını bul
max_dd_idx = int(np.argmax(drawdowns))
max_dd = drawdowns[max_dd_idx]
peak_val = peaks[max_dd_idx]
trough_val = balances[max_dd_idx]

# Peak'e ulaşılan satır
peak_row_idx = -1
for i, b in enumerate(balances):
    if b == peak_val:
        peak_row_idx = i
        break

print("=== DRAWDOWN DETAYLI ANALİZ ===")
print(f"Max DD noktasi: Pozisyon #{max_dd_idx+1}")
print(f"Peak bakiye: ${peak_val:.2f} (Pozisyon #{peak_row_idx+1})")
print(f"Dip bakiye: ${trough_val:.2f}")
print(f"Drawdown: %{max_dd:.2f} (peak'ten dibe)")
print()

min_balance = min(balances)
min_idx = balances.index(min_balance)
print(f"En dusuk bakiye: ${min_balance:.2f} (Pozisyon #{min_idx+1})")

# Peak etrafı
print(f"\n--- Peak etrafi ---")
for i in range(max(0, peak_row_idx-2), min(len(balances), peak_row_idx+3)):
    r = df.iloc[i]
    marker = " <<< PEAK" if i == peak_row_idx else ""
    sym = str(r['symbol'])[:22]
    print(f"  #{i+1:3d} | {sym:22s} | PnL: ${r['total_pnl_usd']:+8.2f} | Bakiye: ${balances[i]:8.2f} | DD: %{drawdowns[i]:.1f}{marker}")

# Max DD etrafı
print(f"\n--- Max DD etrafi ---")
for i in range(max(0, max_dd_idx-5), min(len(balances), max_dd_idx+3)):
    r = df.iloc[i]
    marker = " <<< MAX DD" if i == max_dd_idx else ""
    sym = str(r['symbol'])[:22]
    print(f"  #{i+1:3d} | {sym:22s} | PnL: ${r['total_pnl_usd']:+8.2f} | Bakiye: ${balances[i]:8.2f} | Peak: ${peaks[i]:8.2f} | DD: %{drawdowns[i]:.1f}{marker}")

# Min bakiye etrafı
print(f"\n--- Min bakiye etrafi ---")
for i in range(max(0, min_idx-3), min(len(balances), min_idx+3)):
    r = df.iloc[i]
    marker = " <<< MIN" if i == min_idx else ""
    sym = str(r['symbol'])[:22]
    print(f"  #{i+1:3d} | {sym:22s} | PnL: ${r['total_pnl_usd']:+8.2f} | Bakiye: ${balances[i]:8.2f}{marker}")

# Bakiye $1000 altında kaldığı dönemler
below_1000 = [(i, balances[i]) for i in range(len(balances)) if balances[i] < 1000]
print(f"\n=== BAKIYE $1000 ALTINA DUSTUGU DONEMLER ===")
print(f"Toplam {len(below_1000)} pozisyonda bakiye $1000 altindaydi")
if below_1000:
    print(f"  Ilk: #{below_1000[0][0]+1} (${below_1000[0][1]:.2f})")
    print(f"  Son: #{below_1000[-1][0]+1} (${below_1000[-1][1]:.2f})")
    print(f"  En dusuk: ${min([b for _, b in below_1000]):.2f}")

# ASIL MESELE: Peak kardan mı oluştu?
print(f"\n=== DRAWDOWN PERSPEKTİF ===")
print(f"Peak bakiye: ${peak_val:.2f} (kar: ${peak_val - 1000:.2f})")
print(f"DD dip bakiye: ${trough_val:.2f} (kar: ${trough_val - 1000:.2f})")
print(f"Kardan kaybedilen: ${peak_val - trough_val:.2f}")
if trough_val >= 1000:
    print(f">>> ANAPARA HIC ZARAR GORMEDI! Tamami kardan geri verildi.")
else:
    print(f">>> Anaparadan kaybedilen: ${1000 - trough_val:.2f}")
    print(f">>> Kardan kaybedilen: ${peak_val - 1000:.2f}")

# Bakiye $1000 altına ne zaman düştü, ne zaman çıktı?
print(f"\n=== BAKIYE EĞRISI OZET (her 50 pozisyonda) ===")
for i in range(0, len(balances), 50):
    print(f"  Pozisyon #{i+1:3d}: Bakiye ${balances[i]:8.2f} | Peak ${peaks[i]:8.2f} | DD %{drawdowns[i]:.1f}")
print(f"  Pozisyon #{len(balances):3d}: Bakiye ${balances[-1]:8.2f} | Peak ${peaks[-1]:8.2f} | DD %{drawdowns[-1]:.1f}")

# Drawdown'un %20'yi geçtiği dönemler
print(f"\n=== DD > %20 OLAN DONEMLER ===")
in_dd = False
dd_start = 0
for i, dd in enumerate(drawdowns):
    if dd > 20 and not in_dd:
        in_dd = True
        dd_start = i
    elif dd < 5 and in_dd:
        in_dd = False
        print(f"  #{dd_start+1} - #{i+1}: Max DD %{max(drawdowns[dd_start:i+1]):.1f} | Bakiye ${balances[dd_start]:.2f} -> ${balances[i]:.2f}")
if in_dd:
    print(f"  #{dd_start+1} - #{len(balances)}: Max DD %{max(drawdowns[dd_start:]):.1f} | Bakiye ${balances[dd_start]:.2f} -> ${balances[-1]:.2f}")
