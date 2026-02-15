# 📋 CHANGELOG - Crypto Trading Bot

## [v3.0.4] - 2026-02-14

### ✨ Yeni Özellikler
- **Trade History API:** Borsadaki tüm işlem geçmişini JSON (`/trades`) veya CSV (`/download-trades`) formatında indirme desteği eklendi.

### 🛠 Düzeltmeler
- **Portfolio Sync:** `TradingStrategy` -> `Strategy` sınıf adı çakışması giderildi.
- **Entry Price Sync:** Borsadaki gerçek maliyet ile bot hafızası arasındaki senkronizasyon %100 uyumlu hale getirildi.
- **Northflank Port:** Statik port yerine dinamik `$PORT` kullanımına geçildi.

---

## [v3.0.0] - 2026-02-14

### 🚀 Northflank & All-in-One Mimarisi
- **Tek Konteyner Tasarımı:** Redis, Monitoring API ve Trading Worker tek bir Docker konteynerinde birleştirildi (Northflank kaynak tasarrufu için).
- **FastAPI İzleme:** Bot durumunu (istatistikler, açık pozisyonlar, aday coinler) canlı takip etmek için API eklendi.
- **Docker Optimizasyonu:** `Dockerfile` ve `entrypoint.sh` Linux/Windows uyumluluğu (LF temizliği) ve performans için güncellendi.

### 🛠 Kritik Hata Düzeltmeleri
- **KeyError (Sinyal Log):** Sinyal loglarında `action` yerine `side` kullanılarak botun çökmesi engellendi.
- **NaN ATR Koruması:** ATR indikatörü oluşmamış coinlerde `%1` varsayılan değer kullanılarak `NaN` kaynaklı SL/TP hataları giderildi.
- **Marjin Kurtarma:** Re-start sonrası borsadan çekilen pozisyonların marjin miktarı kaldıraca göre otomatik hesaplanarak PnL takibi düzeltildi.
- **Binance -4130 (SL Çatışması):** TP1/TP2 sonrası yeni SL koymadan önce eski emirlerin temizlenmesi ve kısa bekleme süresi eklendi.
- **Aktif Sembol Filtresi:** `BNXUSDT` gibi statüsü `TRADING` olmayan veya inaktif olan coinler tarama listesinden tamamen çıkarıldı.

### 📈 Geliştirmeler
- **Telegram Timeout:** Stabil olmayan bağlantılar için bildirim timeout süresi 15 saniyeye çıkarıldı.
- **Debug Logları:** Telegram hataları için detaylı traceback eklenerek teşhis kolaylaştırıldı.
- **Requirements:** Bağımlılıklar güncellendi ve `.venv` uyumluluğu sağlandı.

---

## [v1.3.1] - 2026-02-11

### 🧪 SOL Agresif Backtest Testi

#### Yeni Dosya: sol_test.py
- **SOL Coin Agresif Backtest:** $200 başlangıç, 10x kaldıraç, tüm bakiye ile test
- **Tarih Aralığı:** 15 Ocak - 10 Şubat 2026
- **Günde Min 5 İşlem Hedefi:** Akıllı giriş puanlaması ile zorunlu işlem açma
- **Kademeli TP Sistemi:**
  - TP1: 1:1 RR → %50 pozisyon kapat
  - TP2: 1:1.8 RR → %30 pozisyon kapat
  - TP3: 1:2.5 RR → %20 pozisyon kapat
- **Sıkı SL:** ATR × 1.2 (~%1.8 fiyat hareketi)
- **Max Kayıp Limiti:** Tek işlemde max %15 kayıp
- **BTC Trend Takibi:** BTC yönüne göre LONG/SHORT tercih
- **Trailing SL:** TP1 hit sonrası SL entry seviyesine çekilir
- **Cooldown Sistemi:** Kayıptan sonra 1.5 saat, kazançtan sonra 30 dk bekleme
- **4 Saat Timeout:** Max 16 mum (4 saat) pozisyon tutma

---

## [v1.3.0] - 2026-02-11

### 🏆 Top Performer Coin Listesi ve Backtest Optimizasyonu

#### swing_bot.py Güncellemeleri
- **Top 20 Performer Listesi Eklendi:** 1-8 Şubat backtest sonuçlarına göre en başarılı 20 coin belirlendi
  - ENSO (+233.6%), ASTER (+185.5%), WHITEWHALE (+183.6%), PIPPIN (+173.6%), GPS (+167.9%)...
  - `USE_TOP_PERFORMERS = True` ile sadece kanıtlanmış coinler taranıyor
- **BTC Trend Ağırlığı Optimize Edildi:** 
  - BTC aynı yön bonus: +15p (önceden +20p)
  - BTC ters yön cezası: -8p (önceden -15p, hafifletildi)
- **Score Threshold Güncellendi:** 60 → 70 (daha kaliteli sinyaller)
- **Strong Signal Threshold:** 75 (yüksek kaldıraç için)
- **Funding Rate, Open Interest, Taker Ratio** piyasa verileri eklendi

#### backtest_swing.py - Kapsamlı Backtest Motoru
- **Çift Yönlü Backtest:** Hem LONG hem SHORT işlemler backteste dahil
- **Farklı Score Eşikleri:** Long=65, Short=75 (asimetrik yaklaşım)
- **Min Score Fark:** LONG-SHORT arası en az 20 puan fark zorunlu
- **Optimize Edilmiş TP/SL:**
  ```
  SL: ATR × 1.5 (önceden 2.0, daha sıkı)
  TP1: 1:1.2 (40% pozisyon kapatma)
  TP2: 1:2.0 (35% pozisyon kapatma)
  TP3: 1:3.0 (25% pozisyon kapatma)
  ```
- **24 Saat Timeout:** Zararda kapanan coinlerde 24 saat işlem yasağı
- **BTC Trend Zorunluluğu:** EMA50/EMA200 dizilimine göre yön kilitleme
  - BTC boğada → sadece LONG açılır
  - BTC ayıda → sadece SHORT açılır
- **Sharpe Ratio** hesaplaması eklendi
- **Sinyal CSV Export:** Tüm sinyaller `swing_signals.csv`'ye kaydediliyor (778 sinyal)

#### veri_cek.py Güncellemeleri
- **Veri Aralığı Genişletildi:** 15 gün → 60 gün (2 ay)
- **Coin Aralığı Genişletildi:** Rank 50-100 → Rank 1-100 (ilk 100 coin)
- **Pagination Desteği:** 1000'lik batchler ile büyük veri çekme
- **Hedef Tarih Aralığı:** 2026-01-12 - 2026-01-21

#### Yeni Dosyalar
- **canli_analiz.py** - Canlı piyasa analiz scripti
  - Top performer coinleri anlık tarama
  - BTC trend analizi + en iyi sinyal seçimi
  - Konsol çıktısı ile quick-look analiz
- **long_score_test.py** - Long skor test scripti
  - Düşüş piyasasında long skor davranışı testi
  - BTC EMA50/EMA200 trend filtresi doğrulama
- **swing_signals.csv** - 778 backtest sinyali kaydı

### 📊 Backtest Sonuçları (12-21 Ocak 2026)
```
📅 Test Periyodu: 12-21 Ocak 2026 (1 ay önceki hafta)
💰 Başlangıç: $1,000
⚡ Kaldıraç: 5x-10x (dinamik)
📊 Pozisyon: %10
```

---

## [v1.2.0] - 2026-02-10

### 🔄 Trendle Uyumlu İşlem Zorunluluğu ve BTC Trend Algoritması
- **BTC Trend Algoritması Geliştirildi:** Son 50 mumun EMA50 ve EMA200 dizilimine bakılarak boğa/ayı trendi belirleniyor.
- **Trendle Ters Yönde İşlem Engellendi:** BTC boğa trendde sadece long, ayı trendde sadece short işlemler açılıyor. Ters yöndeki işlemler tamamen engellendi.
- **Backtest ve canlıda trendle uyumlu, daha güvenli işlem açma.**
- **Kod ve parametreler güncellendi.**

### 🚀 Yeni: Swing Bot (Çift Yönlü)

#### swing_bot.py - BTC Takipli Çift Yönlü Trading
- **BTC Trend Analizi**: Önce BTC yönü belirleniyor (BULLISH/BEARISH/NEUTRAL)
- **Çift Yönlü Sinyal**: Hem LONG hem SHORT sinyalleri
- **Dinamik Kaldıraç**: 5x-10x (sinyal gücüne göre)
- **Pozisyon Süresi**: 1-4 saat (daha stabil)
- **Multi-Timeframe**: 15m, 1h, 4h confluence

#### Strateji Parametreleri
```
Min Score: 60
Min Win Rate: 65%
BTC Aynı Yön Bonus: +20p
BTC Ters Yön Ceza: -15p

Kaldıraç:
  • Score≥90 + WR≥75%: 10x
  • Score≥80 + WR≥70%: 8x
  • Score≥70 + WR≥65%: 7x
  • Score≥60: 6x

Stop Loss: ATR × 2.0
TP1: 1:1.5 (30%)
TP2: 1:2.5 (30%)
TP3: 1:4.0 (40%)
```

#### LONG Sinyal Kriterleri
- Golden Cross (EMA9 > EMA21)
- RSI < 30 (aşırı satım)
- MACD Bullish Cross
- BB Alt Bant Bounce
- StochRSI < 20

#### SHORT Sinyal Kriterleri  
- Death Cross (EMA9 < EMA21)
- RSI > 80 (aşırı alım)
- MACD Bearish Cross
- BB Üst Bant Reddi
- StochRSI > 85

---

## [v1.1.0] - 2026-02-10

### 🚀 Yeni: Swing Bot (Çift Yönlü)

#### swing_bot.py - BTC Takipli Çift Yönlü Trading
- **BTC Trend Analizi**: Önce BTC yönü belirleniyor (BULLISH/BEARISH/NEUTRAL)
- **Çift Yönlü Sinyal**: Hem LONG hem SHORT sinyalleri
- **Dinamik Kaldıraç**: 5x-10x (sinyal gücüne göre)
- **Pozisyon Süresi**: 1-4 saat (daha stabil)
- **Multi-Timeframe**: 15m, 1h, 4h confluence

#### Strateji Parametreleri
```
Min Score: 60
Min Win Rate: 65%
BTC Aynı Yön Bonus: +20p
BTC Ters Yön Ceza: -15p

Kaldıraç:
  • Score≥90 + WR≥75%: 10x
  • Score≥80 + WR≥70%: 8x
  • Score≥70 + WR≥65%: 7x
  • Score≥60: 6x

Stop Loss: ATR × 2.0
TP1: 1:1.5 (30%)
TP2: 1:2.5 (30%)
TP3: 1:4.0 (40%)
```

#### LONG Sinyal Kriterleri
- Golden Cross (EMA9 > EMA21)
- RSI < 30 (aşırı satım)
- MACD Bullish Cross
- BB Alt Bant Bounce
- StochRSI < 20

#### SHORT Sinyal Kriterleri  
- Death Cross (EMA9 < EMA21)
- RSI > 80 (aşırı alım)
- MACD Bearish Cross
- BB Üst Bant Reddi
- StochRSI > 85

---

## [v1.0.0] - 2026-02-09

### 🚀 Yeni Özellikler

#### Trading Bot Sistemleri
- **short_bot.py** - SHORT sinyal trading botu oluşturuldu
  - 9 teknik indikatör entegrasyonu (ADX, DI+/DI-, EMA9/21, SMA50, RSI, MACD, BB, StochRSI, MFI, ATR)
  - Multi-timeframe analiz (15m, 1h, 4h)
  - Telegram bildirim sistemi
  
- **ultra_short_bot.py** - Geliştirilmiş ultra short bot
  - Daha agresif sinyal algılama
  - Hızlı giriş/çıkış stratejisi

- **oto_bot.py** - Otomatik trading bot altyapısı

- **scan_50_100.py** - Coin tarama scripti
  - Hacme göre 50-100 sıralı coinleri tarar
  - En iyi 3 SHORT sinyalini Telegram'a gönderir
  - 61/100 coin'de sinyal bulundu (LA %90, KITE %88, 42 %87)

#### Backtest Sistemleri
- **backtest_dun.py** - İlk backtest scripti
  - Başlangıç: -19% kayıp (sorunlu strateji)
  
- **backtest_csv.py** - Hızlı CSV tabanlı backtest (v3)
  - ⚡ ~0.5 saniyede backtest (vs dakikalar)
  - SINGLE_COIN filtresi ile tek coin test
  - SHOW_TRADE_DETAILS detaylı işlem logu
  - Tarih aralığı: 2026-01-25 - 2026-02-08

#### Veri Yönetimi
- **veri_cek.py** - OHLCV veri çekme scripti
  - 15 günlük 15m mum verisi
  - 51 coin için veri indirildi (rank 50-100)
  - CSV formatında kayıt
  - Bybit/OKX/Binance desteği (bağlantı sorunları nedeniyle)

- **backtest_data/** klasörü
  - 51 coin CSV dosyası
  - `_coin_list.csv` metadata dosyası

### 📈 Strateji Geliştirmeleri

#### v1 → v2 İyileştirmeler
| Sorun | Çözüm |
|-------|-------|
| Re-entry spam | 8 mum cooldown eklendi |
| Sıkı stop loss | ATR × 2.5 genişletildi |
| Kötü R:R oranı | Partial TP sistemi |

#### v3 Final Strateji Parametreleri
```
Score Threshold: ≥80
Win Rate Threshold: ≥75%
Cooldown: 8 mum
Max Trades/Coin: 20

Stop Loss: ATR × 2.5
TP1: 1:1.5 (30% pozisyon)
TP2: 1:2.5 (30% pozisyon)  
TP3: 1:4.0 (40% pozisyon)

Volatilite Filtresi: 0.5% < ATR% < 5%
Trailing Stop: TP1/TP2 sonrası aktif
```

### 📊 Backtest Sonuçları

#### Haftalık Test (1-8 Şubat 2026)
| Metrik | Değer |
|--------|-------|
| Toplam İşlem | 304 |
| Win Rate | 58.6% |
| Başlangıç | $1,000 |
| Final | $1,821 |
| **Kar** | **+$821 (+82%)** |

#### Tekil Coin Performansları
| Coin | İşlem | Win Rate | Kar | TP3 | Stop Loss |
|------|-------|----------|-----|-----|-----------|
| **DOT** | 21 | **81%** | **+$201** | 4 | 2 |
| AAVE | 16 | 75% | +$163 | 3 | 3 |
| HBAR | 15 | 60% | +$29 | 2 | 5 |

### 🔧 Teknik Detaylar

#### Kullanılan Kütüphaneler
- `ccxt` - Kripto borsa API
- `pandas` - Veri işleme
- `pandas_ta` - Teknik analiz
- `requests` - HTTP istekleri

#### Telegram Entegrasyonu
- Bot Token: `8063148867:AAH2UX__...`
- Chat ID: `6786568689`
- Sinyal ve backtest sonuçları gönderimi

#### İndikatör Listesi (9 adet)
1. ADX + DI+/DI- (trend gücü)
2. EMA 9 (hızlı trend)
3. EMA 21 (orta trend)
4. SMA 50 (yavaş trend)
5. RSI (momentum)
6. MACD (trend değişimi)
7. Bollinger Bands (volatilite)
8. Stochastic RSI (aşırı alım/satım)
9. MFI (para akışı)

### 🐛 Çözülen Sorunlar
- Binance API bağlantı sorunları (SSL reset)
- Re-entry spam problemi (cooldown ile çözüldü)
- Düşük win rate (-19% → +82% karlılık)
- Yavaş backtest (dakikalar → 0.5 saniye)

### 📁 Proje Yapısı
```
murat/
├── backtest_bot.py      # Eski backtest
├── backtest_csv.py      # Hızlı CSV backtest ⭐
├── backtest_dun.py      # Günlük backtest
├── eth_analiz.py        # ETH analiz
├── oto_bot.py           # Otomatik bot
├── sample_.py           # Örnek kod
├── scan_50_100.py       # Coin tarayıcı
├── short_bot.py         # SHORT bot
├── temp_bnb.py          # BNB test
├── ultra_short_bot.py   # Ultra short bot
├── veri_cek.py          # Veri çekici
├── CHANGELOG.md         # Bu dosya
└── backtest_data/       # 51 coin CSV verisi
    ├── _coin_list.csv
    ├── DOT_USDT_USDT.csv
    ├── AAVE_USDT_USDT.csv
    └── ... (48 diğer coin)
```

### 🔗 Repository
- GitHub: https://github.com/Golabstech/bugra-bot
- Push tarihi: 2026-02-09
- 64 dosya, 76,209 satır kod

---

## Sonraki Adımlar (Planlar)

## [3.1.0] - 2026-02-15

## [3.2.0] - 2026-02-15

### ✨ Features
- add conventional commits and semantic versioning
- Add API-controlled replay mode for live engine backtesting

### ✨ Features
- add conventional commits and semantic versioning
- Add API-controlled replay mode for live engine backtesting
- [x] İlk 100 coin için 2 aylık veri çekimi (veri_cek.py güncellendi)
- [x] LONG sinyal stratejisi ekleme (swing_bot.py çift yönlü)
- [x] Top performer coin listesi oluşturma
- [x] Canlı analiz scripti (canli_analiz.py)
- [ ] Canlı otomatik trading modu (API entegrasyonu)
- [ ] Web dashboard
- [ ] Risk yönetimi modülü (max drawdown limiti, günlük kayıp limiti)
- [ ] Backtest sonuçlarını otomatik Telegram'a gönderme

---
*Son güncelleme: 2026-02-11*
