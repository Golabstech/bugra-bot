import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import time
from datetime import datetime

# ==========================================
# AYARLAR (KULLANICI TANIMLI DEĞİŞKENLER)
# ==========================================
API_KEY = 'YOUR_API_KEY_HERE'
SECRET_KEY = 'YOUR_SECRET_KEY_HERE'
TELEGRAM_TOKEN = '8063148867:AAH2UX__oKRPtXGyZWtBEmMJOZOMY1GN3Lc'
CHAT_ID = '6786568689'

# Strateji Ayarları
TIMEFRAME = '1h'          # "Asansör" stratejisi için 1 saatlik grafik şart.
LEVERAGE = "5x"           # Güvenli kaldıraç sınırı.
SCORE_THRESHOLD = 80      # Sinyal için gereken minimum puan.
MAX_SIGNALS_PER_HOUR = 5  # Bir taramada gönderilecek maks sinyal.

# ==========================================
# BORSA BAĞLANTISI
# ==========================================
exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: print("Telegram hatası!")

def get_market_context():
    """BTC Dominansı ve Genel Piyasa Havasını ölçer."""
    tickers = exchange.fetch_tickers()
    btc_price = tickers['BTC/USDT']['last']
    # Basit bir dominans ve trend tahmini
    btc_change = tickers['BTC/USDT']['percentage']
    return btc_change, btc_price

def calculate_fibonacci(df):
    """Son 100 mumun en yüksek/düşük seviyelerine göre Fib 0.618 seviyesini bulur."""
    high = df['high'].tail(100).max()
    low = df['low'].tail(100).min()
    return low + (high - low) * 0.618

def analyze_symbol(symbol, rank):
    """1 Saatlik grafikte derin analiz ve puanlama yapar."""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # İndikatörler
        df['ema9'] = ta.ema(df['close'], length=9)
        df['ma21'] = ta.sma(df['close'], length=21)
        df['rsi'] = ta.rsi(df['close'], length=14)
        bb = ta.bbands(df['close'], length=20, std=2)
        df['bb_u'] = bb['BBU_20_2.0']
        df['bb_l'] = bb['BBL_20_2.0']
        df['bb_m'] = bb['BBM_20_2.0']
        macd = ta.macd(df['close'])
        df['macd'] = macd['MACD_12_26_9']
        df['macd_s'] = macd['MACDs_12_26_9']
        stoch = ta.stoch(df['high'], df['low'], df['close'])
        df['st_k'] = stoch['STOCHk_14_3_3']
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        fib618 = calculate_fibonacci(df)
        
        score = 0
        direction = "WAIT"

        # --- LONG PUANLAMA ---
        if last['close'] <= last['bb_l']: score += 20 # BB Alt Bant
        if last['rsi'] < 35: score += 15             # RSI Dip
        if last['st_k'] < 20: score += 15            # Stoch Dip
        if last['close'] >= fib618 * 0.99: score += 20 # Fib Desteği
        if last['macd'] > last['macd_s']: score += 15 # MACD Pozitif
        if last['ema9'] > last['ma21']: score += 15   # EMA Cross

        if score >= SCORE_THRESHOLD: direction = "LONG"

        # --- SHORT PUANLAMA (Eğer Long değilse) ---
        if direction == "WAIT":
            s_score = 0
            if last['close'] >= last['bb_u']: s_score += 25 # BB Üst Bant (Asansör girişi)
            if last['rsi'] > 65: s_score += 15             # RSI Tepe
            if last['st_k'] > 80: s_score += 15            # Stoch Tepe
            if last['macd'] < last['macd_s']: s_score += 20 # MACD Negatif
            if last['ema9'] < last['ma21']: s_score += 25   # EMA Cross (Asansör düşüş onayı)
            
            if s_score >= SCORE_THRESHOLD:
                direction = "SHORT"
                score = s_score

        return {
            'symbol': symbol, 'direction': direction, 'score': score, 
            'rank': rank, 'price': last['close'], 'bb_m': last['bb_m'],
            'stop': last['bb_u'] if direction == "SHORT" else last['bb_l']
        }
    except: return None

def main():
    send_telegram("🤖 *Bot Aktif!* 1H 'Asansör' Stratejisi Başlatıldı.")
    
    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Tarama Başlıyor...")
            tickers = exchange.fetch_tickers()
            sorted_symbols = sorted(
                [s for s in tickers if '/USDT' in s and ':' not in s],
                key=lambda x: tickers[x]['quoteVolume'], reverse=True
            )

            found_signals = 0
            # 100-200, 200-300, 300-400 Kademeli Tarama
            for start, end in [(100, 200), (200, 300), (300, 400)]:
                if found_signals >= MAX_SIGNALS_PER_HOUR: break
                
                batch = sorted_symbols[start:end]
                for i, symbol in enumerate(batch):
                    if found_signals >= MAX_SIGNALS_PER_HOUR: break
                    
                    rank = start + i + 1
                    analysis = analyze_symbol(symbol, rank)
                    
                    if analysis and analysis['direction'] != "WAIT":
                        icon = "🟢" if analysis['direction'] == "LONG" else "🔴"
                        msg = (
                            f"{icon} *#{analysis['symbol'].split('/')[0]} - {analysis['direction']} ({LEVERAGE})*\n"
                            f"⭐ *PUAN:* {analysis['score']}/100\n"
                            f"🏆 *SIRA:* {analysis['rank']}\n"
                            f"━━━━━━━━━━━━━━━\n"
                            f"📥 *GİRİŞ:* {analysis['price']:.4f}\n"
                            f"🛡️ *DESTEK/DİRENÇ:* {analysis['bb_m']:.4f}\n"
                            f"🛑 *STOP:* {analysis['stop']:.4f}\n"
                            f"📢 *ÇIKIŞ:* Veri 'Sell' diyene kadar bekle!"
                        )
                        send_telegram(msg)
                        found_signals += 1
                        time.sleep(1) # Telegram limit
            
            print(f"Tarama bitti. {found_signals} sinyal bulundu. 1 saat bekleniyor...")
            time.sleep(3600) # Saatlik grafik olduğu için saat başı tara
            
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()