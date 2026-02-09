import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import time
import sys
from datetime import datetime

# ==========================================
# ⚙️ ULTRA SHORT BOT - MULTI TIMEFRAME
# ==========================================
API_KEY = 'YOUR_API_KEY_HERE'
SECRET_KEY = 'YOUR_SECRET_KEY_HERE'
TELEGRAM_TOKEN = '8063148867:AAH2UX__oKRPtXGyZWtBEmMJOZOMY1GN3Lc'
CHAT_ID = '6786568689'

# Strateji Ayarları
TIMEFRAMES = ['1d', '1h', '15m']  # Multi-timeframe analiz
LEVERAGE_MSG = "5x"               # Kaldıraç uyarısı
SCORE_THRESHOLD = 55              # Minimum Sinyal Puanı (düşürüldü - daha fazla fırsat)
STRONG_SIGNAL_THRESHOLD = 75      # Güçlü sinyal eşiği
MAX_SIGNALS_PER_HOUR = 10         # Saat başı maks sinyal
MIN_VOLUME_USD = 40_000_000       # Minimum hacim: 40M USD
SCAN_COIN_COUNT = 100             # Taranacak coin sayısı
MIN_WIN_RATE = 60                 # Minimum Win Rate %

# Timeframe Güvenilirlik Ayarları
TF_RELIABILITY = {
    '1d': 10,   # Günlük = En güvenilir
    '1h': 5,    # Saatlik = Orta
    '15m': -5   # 15dk = Daha riskli
}

# ==========================================
# 🔌 BORSA BAĞLANTISI
# ==========================================
try:
    exchange_config = {
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    }
    
    if API_KEY != 'YOUR_API_KEY_HERE':
        exchange_config['apiKey'] = API_KEY
        exchange_config['secret'] = SECRET_KEY
    else:
        print("ℹ️ API Anahtarı girilmedi. Bot 'Public Mod'da çalışacak (Sadece izleme).")

    exchange = ccxt.binance(exchange_config)
except Exception as e:
    print(f"Bağlantı Hatası: {e}")
    sys.exit()

# ==========================================
# 🛠️ YARDIMCI FONKSİYONLAR
# ==========================================

def send_telegram_message(message):
    """Telegram üzerinden mesaj gönderir."""
    if TELEGRAM_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN':
        print(f"TELEGRAM: {message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def get_funding_rate(symbol):
    """Binance Futures Funding Rate verisini çeker."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={clean_symbol}&limit=1"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list) and len(response) > 0:
            return float(response[0]['fundingRate'])
        return 0.0
    except:
        return 0.0

def get_binance_whale_sentiment(symbol):
    """Binance Top Trader Long/Short Ratio verisini çeker."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={clean_symbol}&period=1h&limit=1"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list):
            return float(response[0]['longShortRatio'])
        return 1.0
    except:
        return 1.0

def get_global_long_short_ratio(symbol):
    """Tüm kullanıcıların Long/Short oranını çeker."""
    try:
        clean_symbol = symbol.replace('/', '').split(':')[0]
        url = f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={clean_symbol}&period=1h&limit=1"
        response = requests.get(url, timeout=5).json()
        if response and isinstance(response, list):
            return float(response[0]['longShortRatio'])
        return 1.0
    except:
        return 1.0

def calculate_risk_reward(entry, stop, direction="SHORT"):
    """Risk/Reward oranına göre TP'leri hesaplar."""
    risk = abs(entry - stop)
    tp1 = entry - (risk * 1.5)  # 1:1.5 R:R
    tp2 = entry - (risk * 2.5)  # 1:2.5 R:R
    tp3 = entry - (risk * 4)    # 1:4 R:R
    return tp1, tp2, tp3

# ==========================================
# 🧠 SHORT ANALİZ MOTORU
# ==========================================

def analyze_short(symbol, rank):
    """
    SHORT Analiz Motoru
    İndikatörler: Bollinger, ADX, MACD, MA, RSI
    Maksimum Puan: 150
    """
    try:
        # Veri Çekme (retry mekanizması ile)
        ohlcv = None
        for attempt in range(3):
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=150)
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(1)
                    continue
                else:
                    return None
        
        if not ohlcv or len(ohlcv) < 100:
            return None

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # ═══════════════════════════════════════════════════════════════
        # İNDİKATÖR HESAPLAMALARI
        # ═══════════════════════════════════════════════════════════════
        
        # 1. Moving Averages (MA)
        df['ma20'] = ta.sma(df['close'], length=20)
        df['ma50'] = ta.sma(df['close'], length=50)
        df['ema9'] = ta.ema(df['close'], length=9)
        df['ema21'] = ta.ema(df['close'], length=21)
        
        # 2. RSI (14)
        df['rsi'] = ta.rsi(df['close'], length=14)
        
        # 3. MACD
        macd = ta.macd(df['close'])
        if macd is not None:
            df['macd'] = macd.iloc[:, 0]
            df['macd_signal'] = macd.iloc[:, 1]
            df['macd_hist'] = macd.iloc[:, 2]
        else:
            df['macd'] = df['macd_signal'] = df['macd_hist'] = 0
        
        # 4. Bollinger Bands (20, 2)
        bb = ta.bbands(df['close'], length=20, std=2)
        if bb is not None:
            df['bb_lower'] = bb.iloc[:, 0]
            df['bb_middle'] = bb.iloc[:, 1]
            df['bb_upper'] = bb.iloc[:, 2]
        else:
            df['bb_lower'] = df['close'] * 0.98
            df['bb_middle'] = df['close']
            df['bb_upper'] = df['close'] * 1.02
        
        # 5. ADX + DI
        adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx_data is not None:
            df['adx'] = adx_data.iloc[:, 0]
            df['di_plus'] = adx_data.iloc[:, 1]
            df['di_minus'] = adx_data.iloc[:, 2]
        else:
            df['adx'] = df['di_plus'] = df['di_minus'] = 0
        
        # 6. ATR (Stop Loss için)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # NaN değerleri doldur
        df = df.ffill().fillna(0)
        
        # Son veriler
        last = df.iloc[-1]
        prev = df.iloc[-2]
        current_price = float(last['close'])
        
        # Balina verileri
        whale_ratio = get_binance_whale_sentiment(symbol)
        global_ls_ratio = get_global_long_short_ratio(symbol)
        funding_rate = get_funding_rate(symbol)
        
        # ═══════════════════════════════════════════════════════════════
        # SHORT PUANLAMA (Maks 150 puan)
        # ═══════════════════════════════════════════════════════════════
        short_score = 0
        short_reasons = []
        
        # --- 1. ADX + DI (Trend Gücü) - Maks: 30p ---
        adx = float(last['adx']) if pd.notna(last['adx']) else 0
        di_plus = float(last['di_plus']) if pd.notna(last['di_plus']) else 0
        di_minus = float(last['di_minus']) if pd.notna(last['di_minus']) else 0
        
        if adx > 25 and di_minus > di_plus:
            short_score += 30
            short_reasons.append(f"📉 ADX Güçlü ({adx:.0f}) + DI->DI+: +30p")
        elif adx > 20 and di_minus > di_plus:
            short_score += 20
            short_reasons.append(f"📉 ADX Orta ({adx:.0f}) + DI->DI+: +20p")
        elif di_minus > di_plus * 1.1:
            short_score += 10
            short_reasons.append(f"📉 DI- > DI+: +10p")
        
        # --- 2. MA/EMA Dizilimi - Maks: 25p ---
        ma20 = float(last['ma20']) if pd.notna(last['ma20']) else current_price
        ma50 = float(last['ma50']) if pd.notna(last['ma50']) else current_price
        ema9 = float(last['ema9']) if pd.notna(last['ema9']) else current_price
        ema21 = float(last['ema21']) if pd.notna(last['ema21']) else current_price
        
        # Bearish MA dizilimi
        if ema9 < ema21 < ma20 < ma50:
            short_score += 25
            short_reasons.append("✅ Tam Bearish MA (EMA9<EMA21<MA20<MA50): +25p")
        elif ema9 < ema21 and current_price < ma20:
            short_score += 18
            short_reasons.append("📊 EMA Bearish + Fiyat<MA20: +18p")
        elif current_price < ma20 and current_price < ma50:
            short_score += 12
            short_reasons.append("📊 Fiyat < MA20 & MA50: +12p")
        elif current_price < ema21:
            short_score += 8
            short_reasons.append("📊 Fiyat < EMA21: +8p")
        
        # --- 3. RSI - Maks: 25p ---
        rsi = float(last['rsi']) if pd.notna(last['rsi']) else 50
        
        if rsi > 75:
            short_score += 25
            short_reasons.append(f"🔥 RSI Aşırı Alım ({rsi:.0f}): +25p")
        elif rsi > 65:
            short_score += 18
            short_reasons.append(f"📈 RSI Yüksek ({rsi:.0f}): +18p")
        elif rsi > 55:
            short_score += 10
            short_reasons.append(f"📊 RSI Orta-Yüksek ({rsi:.0f}): +10p")
        
        # --- 4. MACD - Maks: 25p ---
        macd_val = float(last['macd']) if pd.notna(last['macd']) else 0
        macd_sig = float(last['macd_signal']) if pd.notna(last['macd_signal']) else 0
        macd_hist = float(last['macd_hist']) if pd.notna(last['macd_hist']) else 0
        prev_macd_hist = float(prev['macd_hist']) if pd.notna(prev['macd_hist']) else 0
        
        if macd_val < macd_sig and macd_hist < 0:
            short_score += 25
            short_reasons.append("📉 MACD Bearish Cross + Negatif Hist: +25p")
        elif macd_val < macd_sig:
            short_score += 18
            short_reasons.append("📉 MACD < Signal: +18p")
        elif macd_hist < prev_macd_hist and macd_hist < 0:
            short_score += 12
            short_reasons.append("📉 MACD Histogram Düşüyor: +12p")
        
        # --- 5. Bollinger Bands - Maks: 25p ---
        bb_upper = float(last['bb_upper']) if pd.notna(last['bb_upper']) else current_price * 1.02
        bb_middle = float(last['bb_middle']) if pd.notna(last['bb_middle']) else current_price
        bb_lower = float(last['bb_lower']) if pd.notna(last['bb_lower']) else current_price * 0.98
        
        bb_width = (bb_upper - bb_lower) / bb_middle * 100  # BB genişliği %
        
        if current_price >= bb_upper * 0.99:
            short_score += 25
            short_reasons.append(f"🔴 BB Üst Bant Teması: +25p")
        elif current_price > bb_middle and current_price >= bb_upper * 0.97:
            short_score += 18
            short_reasons.append(f"📊 BB Üst Banta Yakın: +18p")
        elif current_price > bb_middle:
            short_score += 8
            short_reasons.append(f"📊 Fiyat > BB Orta: +8p")
        
        # --- 6. Balina/Funding Bonus - Maks: 20p ---
        if whale_ratio < 0.85:
            short_score += 15
            short_reasons.append(f"🐋 Balinalar SHORT ({whale_ratio:.2f}): +15p")
        
        if funding_rate > 0.001:
            short_score += 5
            short_reasons.append(f"💰 Yüksek Funding ({funding_rate*100:.3f}%): +5p")
        
        # ═══════════════════════════════════════════════════════════════
        # KARAR VE SEVİYE HESAPLAMA
        # ═══════════════════════════════════════════════════════════════
        
        if short_score < SCORE_THRESHOLD:
            return None  # Eşik altında sinyal yok
        
        atr = float(last['atr']) if pd.notna(last['atr']) else current_price * 0.02
        stop_loss = current_price + (atr * 1.5)
        tp1, tp2, tp3 = calculate_risk_reward(current_price, stop_loss, "SHORT")
            
        return {
            'symbol': symbol,
            'direction': 'SHORT',
            'score': short_score,
            'price': current_price,
            'stop': stop_loss,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'rank': rank,
            'whale': whale_ratio,
            'global_ls': global_ls_ratio,
            'funding': funding_rate,
            'adx': adx,
            'rsi': rsi,
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'macd_hist': macd_hist,
            'reasons': short_reasons
        }

    except Exception as e:
        print(f"      ❌ HATA ({symbol}): {str(e)}")
        return None

# ==========================================
# 🚀 ANA DÖNGÜ VE TARAMA
# ==========================================

def get_symbols_by_volume():
    """Tüm Futures çiftlerini hacme göre sıralar (Min 40M$)."""
    try:
        tickers = exchange.fetch_tickers()
        pairs = []
        for s, d in tickers.items():
            if '/USDT' in s:
                vol = float(d.get('quoteVolume', 0) or 0)
                if vol >= MIN_VOLUME_USD:
                    pairs.append({'symbol': s, 'volume': vol})
        
        pairs.sort(key=lambda x: x['volume'], reverse=True)
        print(f"   📊 Toplam {len(pairs)} adet Futures çifti bulundu (Hacim > {MIN_VOLUME_USD/1e6:.0f}M$).")
        return [p['symbol'] for p in pairs]
    except Exception as e:
        print(f"Ticker Hatası: {e}")
        return []

def main():
    print(f"🔻 SHORT BOT AKTİF | Timeframe: {TIMEFRAME} | Hedef Puan: {SCORE_THRESHOLD}")
    print(f"📊 Min Hacim: {MIN_VOLUME_USD/1e6:.0f}M$ | İndikatörler: BB, ADX, MACD, MA, RSI")
    send_telegram_message(
        f"🔻 <b>SHORT BOT Başlatıldı!</b>\n"
        f"⏱ Timeframe: {TIMEFRAME}\n"
        f"💰 Min Hacim: {MIN_VOLUME_USD/1e6:.0f}M$\n"
        f"📊 İndikatörler: BB, ADX, MACD, MA, RSI\n"
        f"🎯 Sadece SHORT sinyalleri"
    )

    while True:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M')}] 🔻 SHORT Tarama Başlıyor...")
            all_symbols = get_symbols_by_volume()
            
            signals = []
            analyzed_count = 0
            
            scan_end = min(SCAN_COIN_COUNT, len(all_symbols))
            batch = all_symbols[:scan_end]
            
            print(f"   🔍 İlk {scan_end} coin taranıyor (SHORT için)...")

            for i, symbol in enumerate(batch):
                rank = i + 1
                try:
                    result = analyze_short(symbol, rank)
                    analyzed_count += 1
                    
                    if result:
                        print(f"      🔻 {symbol:<14} | SHORT | Puan: {result['score']}")
                        signals.append(result)
                        
                    if len(signals) >= MAX_SIGNALS_PER_HOUR:
                        break
                        
                except Exception as err:
                    pass
                    
                if (i + 1) % 10 == 0:
                    time.sleep(1)
            
            print(f"   📊 Toplam {analyzed_count} coin analiz edildi, {len(signals)} SHORT sinyal bulundu.")
            
            # Puanı en yüksek olanları öne al
            signals.sort(key=lambda x: x['score'], reverse=True)
            top_signals = signals[:MAX_SIGNALS_PER_HOUR]
            
            if top_signals:
                for s in top_signals:
                    strength = "💪 GÜÇLÜ" if s['score'] >= STRONG_SIGNAL_THRESHOLD else "📊 Normal"
                    
                    reasons_text = "\n".join([f"  • {r}" for r in s['reasons'][:6]])
                    
                    risk_pct = abs(s['price'] - s['stop']) / s['price'] * 100
                    
                    msg = (
                        f"🔻 <b>#{s['symbol'].split('/')[0]} - SHORT ({LEVERAGE_MSG})</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⭐ <b>PUAN:</b> {s['score']}/150 ({strength})\n"
                        f"🏆 <b>Hacim Sırası:</b> #{s['rank']}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"📥 <b>GİRİŞ:</b> ${s['price']:.4f}\n"
                        f"🛑 <b>STOP LOSS:</b> ${s['stop']:.4f} ({risk_pct:.1f}%)\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🎯 <b>TP1:</b> ${s['tp1']:.4f} (R:R 1:1.5)\n"
                        f"🎯 <b>TP2:</b> ${s['tp2']:.4f} (R:R 1:2.5)\n"
                        f"🎯 <b>TP3:</b> ${s['tp3']:.4f} (R:R 1:4)\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>📊 Veriler:</b>\n"
                        f"  🐋 Balina L/S: {s['whale']:.2f}\n"
                        f"  💰 Funding: {s['funding']*100:.4f}%\n"
                        f"  📈 ADX: {s['adx']:.0f} | RSI: {s['rsi']:.0f}\n"
                        f"  📊 BB Üst: ${s['bb_upper']:.4f}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"<b>Sinyal Sebepleri:</b>\n{reasons_text}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⚠️ <i>DYOR - Bu finansal tavsiye değildir</i>"
                    )
                    send_telegram_message(msg)
                    print(f"      📤 Telegram'a gönderildi: {s['symbol']}")
                    time.sleep(1)
            else:
                print("   ❌ Bu turda uygun SHORT sinyal bulunamadı.")
            
            print(f"⏳ 2 Dakika bekleniyor...")
            time.sleep(120)

        except Exception as e:
            print(f"Genel Hata: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
