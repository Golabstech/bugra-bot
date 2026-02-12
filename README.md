# 🤖 Bugra-Bot — Crypto Futures Trading Bot

> Binance Futures üzerinde otomatik short/long sinyal tarama, pozisyon yönetimi ve paper/live trading.

---

## 🏗️ Proje Yapısı

```
bugra-bot/
├── src/
│   ├── bot/                    # 🤖 Canlı Trading Modülleri
│   │   ├── config.py           # Merkezi konfigürasyon (.env)
│   │   ├── exchange.py         # CCXT Binance Futures connector
│   │   ├── strategy.py         # Sinyal motoru (skorlama + filtreler)
│   │   ├── scanner.py          # Top 100 coin tarayıcı
│   │   ├── trader.py           # İşlem yöneticisi (SL/TP/Trailing)
│   │   ├── portfolio.py        # Portföy & risk yönetimi
│   │   ├── notifier.py         # Telegram bildirim servisi
│   │   └── main.py             # Ana bot döngüsü (orchestrator)
│   │
│   └── backtest/               # 📊 Backtest Modülleri
│       ├── engine.py           # Paralel backtest motoru
│       ├── data_fetcher.py     # Bybit OHLCV veri çekici
│       └── analyze_strategy.py # Strateji analiz aracı
│
├── data/                       # 📁 Veri & Sonuçlar (gitignored)
│   ├── backtest_data/          # OHLCV CSV dosyaları
│   ├── backtest_trades.csv     # İşlem logları
│   └── backtest_positions.csv  # Pozisyon özeti
│
├── logs/                       # 📋 Log dosyaları (gitignored)
├── run.py                      # 🚀 Bot giriş noktası
├── .env.example                # API key template
├── requirements.txt            # Python bağımlılıkları
├── CHANGELOG.md                # Sürüm geçmişi
└── README.md                   # Bu dosya
```

---

## 🚀 Kurulum

### 1. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 2. API Key'leri Ayarla

```bash
cp .env.example .env
# .env dosyasını düzenleyip API key'leri girin
```

| Değişken | Açıklama |
|----------|----------|
| `BINANCE_API_KEY` | Binance Futures API key |
| `BINANCE_API_SECRET` | Binance Futures API secret |
| `EXCHANGE_SANDBOX` | `true` = Paper trading, `false` = Canlı |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |

### 3. Botu Başlat

```bash
python run.py
```

---

## ⚙️ Konfigürasyon

Tüm ayarlar `.env` dosyasından veya `src/bot/config.py` varsayılanlarından okunur.

### Risk Yönetimi

| Ayar | Varsayılan | Açıklama |
|------|-----------|----------|
| `MAX_RISK_PCT` | 50 | Kasanın max %'si riske atılabilir |
| `MAX_CONCURRENT_POSITIONS` | 5 | Max eş zamanlı açık pozisyon |
| `DAILY_LOSS_LIMIT_PCT` | 10 | Günlük max kayıp (kasanın %'si) |
| `LEVERAGE` | 5 | Kaldıraç oranı |
| `POSITION_SIZE_PCT` | 10 | Pozisyon başına kasanın %'si |

### Strateji

| Ayar | Varsayılan | Açıklama |
|------|-----------|----------|
| `STRATEGY_SIDE` | SHORT | İşlem yönü (SHORT/LONG) |
| `SCORE_THRESHOLD` | 90 | Minimum sinyal skoru |
| `MIN_REASONS` | 4 | Minimum teknik sinyal sayısı |
| `SL_ATR_MULT` | 2.4 | Stop loss ATR çarpanı |
| `TP1_RR` / `TP2_RR` / `TP3_RR` | 1.8 / 2.8 / 4.5 | Take profit R:R oranları |

### Tarama

| Ayar | Varsayılan | Açıklama |
|------|-----------|----------|
| `SCAN_INTERVAL_SECONDS` | 60 | Tarama döngü aralığı |
| `TIMEFRAME` | 15m | Analiz zaman dilimi |
| `TOP_COINS_COUNT` | 100 | Taranacak coin sayısı |

---

## 🔄 Bot Akışı

```
┌─────────────────────────────────────────────┐
│              ANA DÖNGÜ (60s)                │
│                                             │
│  1. Açık pozisyonları kontrol et (TP/SL)    │
│  2. Top 100 coin'i tara                     │
│  3. Sinyal üret (skor ≥ 90, neden ≥ 4)     │
│  4. Risk kontrolü geç → Pozisyon aç        │
│  5. SL/TP emirlerini borsaya gönder         │
│  6. Telegram bildirimi gönder               │
│                                             │
│  📲 TP1 → Breakeven SL                     │
│  📲 TP2 → Trailing SL + kâra kitle        │
│  📲 TP3 → Tam kapanış                     │
└─────────────────────────────────────────────┘
```

---

## 📊 Backtest

```bash
# Veri çek (Bybit'ten top 100 coin)
python src/backtest/data_fetcher.py

# Backtest çalıştır
python -c "import sys; sys.path.insert(0,'src'); from backtest.engine import run_backtest; run_backtest()"
```

**v1.3.0 Backtest Sonuçları (1 Aylık):**

- Win Rate: %60.3
- Final: $1,312 (+31.21%)
- Monte Carlo %50 Medyan: $2,720
- İflas Riski: %0.00

---

## 📲 Telegram Bildirimleri

| Bildirim | Tetikleyici |
|----------|------------|
| 🎯 Yeni Sinyal | Skor eşiğini geçen coin bulunduğunda |
| 📉 Pozisyon Açıldı | İşlem başarıyla açıldığında |
| ✅ İşlem Kapandı | TP/SL tetiklendiğinde |
| 📊 Günlük Özet | Her gün 00:00 UTC'de |
| 🚨 Hata | Kritik hata oluştuğunda |
| 🛡️ Risk Limiti | Limit aşıldığında |

---

## 🛡️ Güvenlik

- API key'ler `.env` dosyasında saklanır (gitignored)
- Paper trading modu varsayılan olarak aktif
- Günlük kayıp limiti ile otomatik durdurma
- Hard stop loss (%7) ile maksimum kayıp koruması

---

## 📋 Lisans

Private — Golabstech
