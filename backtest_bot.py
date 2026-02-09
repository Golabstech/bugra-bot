import ccxt
import pandas as pd
import pandas_ta as ta
import time
import datetime

def calculate_fibonacci(df, window=100):
    """
    Simulates calculating Fib levels based on the LAST 'window' candles relative to the current row.
    For backtesting, we pass a sliced dataframe representing [start : current_point].
    """
    if len(df) < window:
        # If we don't have enough data, use what we have
        recent_data = df
    else:
        recent_data = df.tail(window)
    
    high_h = recent_data['high'].max()
    low_l = recent_data['low'].min()
    diff = high_h - low_l
    
    fib_0_5 = low_l + (diff * 0.5)
    fib_0_618 = low_l + (diff * 0.618)
    
    return fib_0_5, fib_0_618

def backtest_symbol(symbol, days=2):
    print(f"\n--- Backtesting {symbol} for last {days} days ---")
    try:
        exchange = ccxt.binance({'options': {'defaultType': 'future'}})
        
        # Calculate how many 5m candles in 'days'
        # 1 day = 24 * 12 = 288 candles
        limit = days * 288 
        # Fetch a bit more to have warmup data for indicators
        fetch_limit = limit + 200 
        
        if fetch_limit > 1500: fetch_limit = 1500 # Binance limit
        
        ohlcv = exchange.fetch_ohlcv(symbol, '5m', limit=fetch_limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert timestamp
        df['dt'] = pd.to_datetime(df['timestamp'], unit='ms')

        # --- Calculate Indicators (Vectorized) ---
        df['ema9'] = ta.ema(df['close'], length=9)
        df['ma21'] = ta.sma(df['close'], length=21)
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        macd = ta.macd(df['close'])
        df['macd'] = macd['MACD_12_26_9']
        df['macd_signal'] = macd['MACDs_12_26_9']
        
        bb = ta.bbands(df['close'], length=20, std=2)
        
        # Safe assignment by position to avoid Naming Issues
        # pandas_ta bbands returns 5 columns: BBL, BBM, BBU, BBB, BBP
        df['bb_lower'] = bb.iloc[:, 0]
        df['bb_middle'] = bb.iloc[:, 1]
        df['bb_upper'] = bb.iloc[:, 2]
        
        # Manually calculate stoch since pandas_ta might return different column names depending on version
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
        df['stoch_k'] = stoch['STOCHk_14_3_3']
        df['stoch_d'] = stoch['STOCHd_14_3_3']
        
        # Drop NaN
        df.dropna(inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        signals_found = 0
        
        # Iterate to simulate live bot
        # We start after index 100 to ensure we have enough data for Fib calculation
        for i in range(100, len(df)):
            current_row = df.iloc[i]
            prev_row = df.iloc[i-1]
            
            # Slice dataframe for Fib calculation (simulating "data up to now")
            # We need the last 100 candles ENDING at i
            historical_slice = df.iloc[i-100+1 : i+1] 
            
            fib_5, fib_618 = calculate_fibonacci(historical_slice, window=100)
            
            # --- SCORING LOGIC (Exactly from oto_bot.py) ---
            long_score = 0
            short_score = 0
            current_price = current_row['close']
            
            # 1. Fibonacci
            threshold_pct = 0.005
            details = []
            
            if abs(current_price - fib_5) / fib_5 < threshold_pct:
                details.append("Near Fib 0.5")
                if current_price >= fib_5: long_score += 25
                else: short_score += 25
            elif abs(current_price - fib_618) / fib_618 < threshold_pct:
                details.append("Near Fib 0.618")
                if current_price >= fib_618: long_score += 25
                else: short_score += 25
            
            # 2. Bollinger Bands
            if current_row['low'] <= current_row['bb_lower']:
                long_score += 15
                details.append("BB Lower")
            if current_row['high'] >= current_row['bb_upper']:
                short_score += 15
                details.append("BB Upper")
                
            # 3. Bollinger Volatility
            bb_width = (current_row['bb_upper'] - current_row['bb_lower']) / current_row['bb_middle']
            if bb_width > 0.02:
                long_score += 10
                short_score += 10
            
            # 4. Stoch
            if current_row['stoch_k'] > current_row['stoch_d']:
                long_score += 15
            elif current_row['stoch_k'] < current_row['stoch_d']:
                short_score += 15
            
            # 5. EMA/MA Cross
            if current_row['ema9'] > current_row['ma21']:
                long_score += 15
            else:
                short_score += 15
                
            # 6. RSI
            if current_row['rsi'] < 30:
                long_score += 15
                details.append("RSI Oversold")
            elif current_row['rsi'] > 70:
                short_score += 15
                details.append("RSI Overbought")
                
            # 7. MACD
            if current_row['macd'] > current_row['macd_signal']:
                long_score += 15
            else:
                short_score += 15
                
            # --- EVALUATE ---
            threshold = 80 # Same as bot
            
            if long_score >= threshold:
                print(f"[{current_row['dt']}] LONG Signal! Score: {long_score} | Price: {current_price:.4f} | R: {', '.join(details)}")
                signals_found += 1
            if short_score >= threshold:
                print(f"[{current_row['dt']}] SHORT Signal! Score: {short_score} | Price: {current_price:.4f} | R: {', '.join(details)}")
                signals_found += 1
                
        print(f"Total Signals found in approx {days} days: {signals_found}")
        
    except Exception as e:
        print(f"Error backtesting {symbol}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting Backtest Simulation...")
    # Test on a few volatile and popular pairs
    backtest_symbol('BTC/USDT', days=3)
    backtest_symbol('ETH/USDT', days=3)
    backtest_symbol('SOL/USDT', days=3)
