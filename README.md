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
│     (TP/SL + 🧠 Decay + ⏰ Time Exit)       │
│  3. Top 100 coin'i tara + Funding Rate      │
│  4. Sinyal üret (Skor + BB R:R + Filtreler) │
│  5. Risk kontrolü geç → İnatçı Emir (Retry) │
│  6. SL (Borsada), TP (Dinamik Bollinger)     │
│  7. Telegram bildirimi gönder (Net PnL)     │
│                                             │
│  🛡️ God Candle & Volume Surge Koruması      │
│  🎯 TP1 → Bollinger Mid (%40 + BE SL)       │
│  🎯 TP2 → Bollinger Low/High (%30 + Trailing)│
│  📊 TP3 → Tam Kapanış (%30)                 │
└─────────────────────────────────────────────┘
```

---

## 🚀 Öne Çıkan Özellikler (v2.2.0)

- **🎯 Dinamik Bollinger TP:** Sabit yüzdeler yerine piyasa volatilitesine göre Bollinger bantları (Mid/Low) üzerinden kâr alma.
- **�️ BB R:R Guard:** Bollinger TP hedefi SL riskini karşılamıyorsa (`R:R < 0.5`) işlemi otomatik filtreleme.
- **⏰ Zaman Bazlı Çıkış (Time Exit):** 48 saat boyunca hedefe gitmeyen pozisyonları kapatarak sermaye bağlamasını ve funding kaybını önleme.
- **🧠 Rafine ADX Skorlama:** ADX trend gücünü 3 ana bölgeye ayırarak double-count bug'ını gideren ve daha doğru sinyal üreten mantık.
- **💸 Net PnL (Fee Included):** Tüm kâr/zarar bildirimlerine borsa komisyonlarını (Taker fee) dahil eden gerçekçi raporlama.
- **💪 İnatçı Emir (Retry):** Borsa limitlerine takılan emirlerde otomatik miktar küçültme ve yeniden deneme.
- **🧹 Auto-Sync & Docker:** Borsayla tam senkronizasyon ve Docker/Northflank bulut kurulum desteği.

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
