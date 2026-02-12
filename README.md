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
│              ANA DÖNGÜ (30s)                │
│                                             │
│  1. Portföy Senkronizasyonu & Temizlik      │
│     (Yetim emirleri temizle, bakiye eşle)   │
│  2. Açık pozisyonları kontrol et            │
│     (TP/SL + 🧠 Signal Decay Exit)          │
│  3. Top 100 coin'i tara + Funding Rate      │
│  4. Sinyal üret (Skor + FR + Filtreler)     │
│  5. Risk kontrolü geç → İnatçı Emir (Retry) │
│  6. SL (Borsada), TP (Yazılımsal) ayarla    │
│  7. Telegram bildirimi gönder               │
│                                             │
│  🛡️ God Candle & Volume Surge Koruması      │
│  📈 TP1 → Breakeven SL (%40 Kapat)          │
│  📈 TP2 → Trailing SL (%30 Kapat)           │
│  📊 TP3 → Tam Kapanış (%30)                 │
└─────────────────────────────────────────────┘
```

---

## 🚀 Öne Çıkan Özellikler (v2.1.0)

- **🧠 Signal Decay Exit:** Sinyal gücünü kaybederse (hype biterse) ve kârdaysak otomatik erken çıkış.
- **📊 Funding Rate Alpha:** Piyasa kalabalığını (sentiment) ölçerek ters yönlü (contrarian) işlem avantajı.
- **🛡️ Parabolik Koruma:** God Candle ve Volume Surge filtreleri ile "squeeze" hareketlerine karşı kalkan.
- **🧹 Hibrit TP/SL:** Stop loss borsada (pozisyona bağlı), Take profit'ler yazılımsal yönetimde ( Orphan order sıfırlandı).
- **💪 İnatçı Emir (Retry):** Borsa limitlerine takılan emirlerde otomatik miktar küçültme ve yeniden deneme.

---

## 📊 Backtest

```bash
# Veri çek (Binance'ten top 100 coin)
python src/backtest/data_fetcher.py

# Backtest çalıştır
python -c "import sys; sys.path.insert(0,'src'); from backtest.engine import run_backtest; run_backtest()"
```

**v2.1.0 Backtest Sonuçları (1 Aylık):**

- Win Rate: %58.4
- Final: $1,420 (+42.0%)
- Monte Carlo %50 Medyan: $3,100
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
