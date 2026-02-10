import ccxt
import pandas as pd
import os
import time
from datetime import datetime, timedelta

# ==========================================
# ⚙️ AYARLAR
# ==========================================
DATA_FOLDER = "backtest_data"
DAYS_TO_FETCH = 90          # 3 ay (Bull senaryosu için geniş aralık)
START_RANK = 1              # İlk 100
END_RANK = 100
TIMEFRAME = '15m'

# ==========================================
# 🔌 BORSA BAĞLANTISI (BYBIT)
# ==========================================
exchange = ccxt.bybit({
    'enableRateLimit': True, 
    'timeout': 60000,
    'options': {'defaultType': 'linear'}
})

def get_sorted_coins():
    """Hacme göre sıralı coinleri al"""
    try:
        markets = exchange.load_markets()
        tickers = exchange.fetch_tickers()
        
        futures = []
        for symbol, ticker in tickers.items():
            # Bybit linear format: BTC/USDT:USDT
            if '/USDT:USDT' in symbol and ticker.get('quoteVolume'):
                futures.append({
                    'symbol': symbol, 
                    'volume': float(ticker.get('quoteVolume', 0))
                })
        
        futures.sort(key=lambda x: x['volume'], reverse=True)
        return futures[START_RANK-1:END_RANK]
    except Exception as e:
        print(f"❌ Coin listesi alınamadı: {e}")
        return []

def fetch_ohlcv_with_retry(symbol, tf, since, limit, retries=3):
    """Retry mekanizmalı veri çekme"""
    for attempt in range(retries):
        try:
            data = exchange.fetch_ohlcv(symbol, tf, since=since, limit=limit)
            return data
        except Exception as e:
            if attempt < retries - 1:
                print(f"   ⚠️ Retry {attempt+1}/{retries}...")
                time.sleep(2)
            else:
                return None
    return None

def fetch_and_save_data():
    """90 günlük veriyi çekip CSV'ye kaydet"""
    print("=" * 70)
    print("📥 VERİ ÇEKME VE KAYDETME (GENİŞLETİLMİŞ)")
    print("=" * 70)
    print(f"📅 Son {DAYS_TO_FETCH} günlük veri çekilecek")
    print(f"🎯 Coin aralığı: {START_RANK}-{END_RANK}")
    print(f"⏱️ Timeframe: {TIMEFRAME}")
    print("=" * 70)
    
    # Klasör oluştur
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        print(f"📁 Klasör oluşturuldu: {DATA_FOLDER}")
    
    # Coinleri al
    print("\n📋 Coin listesi alınıyor...")
    coins = get_sorted_coins()
    
    if not coins:
        print("❌ Coin listesi alınamadı!")
        return
    
    print(f"✅ {len(coins)} coin bulundu\n")
    
    # Tarih hesapla
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=DAYS_TO_FETCH)
    start_since = int(start_date.timestamp() * 1000)
    
    saved_count = 0
    coin_list = []
    
    for i, coin in enumerate(coins, 1):
        symbol = coin['symbol']
        safe_symbol = symbol.replace('/', '_').replace(':', '_')
        
        print(f"[{i}/{len(coins)}] {symbol} çekiliyor...", end=" ")
        
        all_ohlcv = []
        current_since = start_since
        
        # Paging mekanizması: Parça parça veri çek
        while current_since < int(datetime.utcnow().timestamp() * 1000):
            data = fetch_ohlcv_with_retry(symbol, TIMEFRAME, current_since, 1000)
            if not data or len(data) == 0:
                break
                
            all_ohlcv.extend(data)
            
            # Son gelen verinin timestamp'ini bir sonraki başlangıç yap
            last_ts = data[-1][0]
            if last_ts == current_since: # Döngüye girmemesi için
                break
            current_since = last_ts + 1
            
            # Rate limit'e takılmamak için kısa bekleme
            time.sleep(0.1)
            
            # Hedef tarihe ulaştıysak dur
            if len(data) < 100: # Daha az veri geldiyse sona yaklaşmışızdır
                break

        if all_ohlcv and len(all_ohlcv) > 100:
            # Tekrar eden verileri temizle
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            
            # CSV'ye kaydet
            filename = f"{DATA_FOLDER}/{safe_symbol}.csv"
            df.to_csv(filename, index=False)
            
            print(f"✅ {len(df)} mum kaydedildi")
            saved_count += 1
            coin_list.append({'symbol': symbol, 'file': filename, 'candles': len(df)})
        else:
            print("❌ Veri alınamadı")
        
        time.sleep(0.2)
    
    # Coin listesini de kaydet
    coin_df = pd.DataFrame(coin_list)
    coin_df.to_csv(f"{DATA_FOLDER}/_coin_list.csv", index=False)
    
    print("\n" + "=" * 70)
    print("✅ VERİ ÇEKME TAMAMLANDI")
    print("=" * 70)
    print(f"📊 Toplam: {saved_count}/{len(coins)} coin kaydedildi")
    print(f"📁 Konum: {DATA_FOLDER}/")
    print(f"📅 Tarih aralığı: {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}")
    print("=" * 70)

if __name__ == "__main__":
    fetch_and_save_data()
