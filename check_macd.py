import pandas as pd
import pandas_ta as ta
import numpy as np

# Sample data
df = pd.DataFrame({'close': np.random.randn(100).cumsum() + 100})
macd = ta.macd(df['close'])
print("MACD DataFrame Columns:")
print(macd.columns.tolist())
