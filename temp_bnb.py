import ccxt
import pandas as pd
import os
from datetime import datetime, timedelta
import time

exchange = ccxt.binance({
    'enableRateLimit': True, 
    'options': {'defaultType': 'future'}
})

# 15 günlük veri çek
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=15)
since = int(start_date.timestamp() * 1000)

print('BNB/USDT verisi çekiliyor...')
time.sleep(1)

try:
    # Futures için BNBUSDT
    data = exchange.fetch_ohlcv('BNB/USDT:USDT', '15m', since=since, limit=1500)
    
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['symbol'] = 'BNB/USDT:USDT'
    
    filepath = 'backtest_data/BNB_USDT_USDT.csv'
    df.to_csv(filepath, index=False)
    
    print(f'Kaydedilen: {len(df)} mum')
    print(f'Dosya var mi: {os.path.exists(filepath)}')
except Exception as e:
    print(f'HATA: {e}')
    print('Alternatif deneniyor...')
    try:
        # Alternatif olarak fapiPublic kullan
        import requests
        url = 'https://fapi.binance.com/fapi/v1/klines'
        params = {
            'symbol': 'BNBUSDT',
            'interval': '15m',
            'startTime': since,
            'limit': 1500
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                                          'close_time', 'quote_volume', 'trades', 'taker_buy_base', 
                                          'taker_buy_quote', 'ignore'])
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
        df['symbol'] = 'BNB/USDT:USDT'
        
        filepath = 'backtest_data/BNB_USDT_USDT.csv'
        df.to_csv(filepath, index=False)
        
        print(f'REST API ile kaydedildi: {len(df)} mum')
    except Exception as e2:
        print(f'Alternatif de basarisiz: {e2}')
