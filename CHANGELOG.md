# 📋 CHANGELOG - Crypto Trading Bot

## [v2.1.0] - 2026-02-12

### 🚀 Gelişmiş Strateji & Risk Yönetimi

#### 🧠 Akıllı Karar Mekanizmaları

- **Funding Rate Alpha:** Piyasa kalabalığını (sentimet) ölçen indikatör entegre edildi. Herkes short iken short açmayı engelleyen (Short Squeeze koruması) ve herkes long iken kontrarian avantaj sağlayan puanlama sistemi eklendi.
- **Signal Decay Exit:** Sinyal gücü giriş seviyesinden %60 aşağı düştüğünde ve pozisyon kârdaysa otomatik kapanış yapan "Zamana Bağlı Çürüme" filtresi eklendi.
- **Top 5 Candidate Log:** Her döngüde sadece sinyalleri değil, en yüksek puanlı ilk 5 aday coini ve neden filtrelendiklerini gösteren şeffaf tarama raporu eklendi.

#### 🛡️ Koruma Filtreleri (Anti-Pump)

- **God Candle Filter:** Ani ve iğnesiz %3+ yükselen dev mumlara karşı giriş engeli.
- **Volume Surge Filter:** Hacim ortalamasının 3.5 katını aşan "breakout" patlamalarına karşı koruma.
- **ATR Volatility Guard:** ATR'nin 3 katını aşan anormal hareketlerde "kafa atmayı" önleyen filtre.

#### 🧹 Altyapı & Robustness

- **Hybrid TP/SL Mimarisi:**
  - **SL:** Pozisyona bağlı `closePosition: true` emir tipine geçildi. Bu sayede stop emirleri Open Orders tabı yerine direkt pozisyonun yanında görünür ve pozisyon kapanınca otomatik silinir (Yetim emir sorunu çözüldü).
  - **TP:** Tamamen yazılımsal yönetime geçildi. Borsa tarafında TP emri bekletilmez, bot fiyatı takip ederek kısmi kapama yapar.
- **İnatçı Emir (Persistent Order):** Borsa miktar/notional limitlerine takılan emirlerde otomatik miktar küçültme ve 3 kez yeniden deneme mekanizması.
- **Orphan Order Cleanup:** Aktif pozisyonu kalmayan coinlerin askıda kalan tüm emirlerini her döngüde otomatik temizleyen süpürge mekanizması.

## [v2.0.0] - 2026-02-12

### 🚀 Live Trading Bot Mimarisi (Stabilizasyon)

#### 🤖 Yeni Modüller (`src/bot/`)

- **`config.py`** — Merkezi konfigürasyon: `.env` dosyasından tüm ayarları okur (API key, risk limitleri, strateji parametreleri)
- **`exchange.py`** — CCXT ile Binance Futures connector: Paper/live mode, pozisyon açma/kapama, SL/TP emirleri, OHLCV çekme, top coin listesi
- **`strategy.py`** — Backtest motorundan taşınan sinyal motoru: Canlı OHLCV verisiyle çalışır, SHORT/LONG skorlama, boğa koruması, ATR volatilite filtresi
- **`scanner.py`** — Market tarayıcı: Top 100 coin'i periyodik olarak tarar, rate limit korumalı
- **`trader.py`** — İşlem yöneticisi: Sinyal → Risk kontrolü → Emir → SL/TP. TP1 sonrası breakeven, TP2 sonrası trailing SL
- **`portfolio.py`** — Portföy & risk yönetimi: Max eş zamanlı pozisyon, günlük kayıp limiti, coin bazlı blacklist/cooldown, dinamik pozisyon boyutlandırma
- **`notifier.py`** — Telegram bildirim servisi: Sinyal, trade açma/kapama, günlük özet, hata ve risk limiti bildirimleri (async httpx)
- **`main.py`** — Ana bot döngüsü: Tüm modülleri orkestra eder, graceful shutdown, günlük özet raporu

#### 📁 Proje Organizasyonu

- `src/bot/` — Canlı trading modülleri
- `src/backtest/` — Backtest modülleri (engine, data_fetcher, analyze)
- `data/` — Backtest verileri ve CSV sonuçları (gitignored)
- `logs/` — Log dosyaları (gitignored)
- `run.py` — Ana giriş noktası
- `.env.example` — API key template
- `requirements.txt` — Python bağımlılıkları

#### 🛡️ Risk Yönetimi Özellikleri

- Max 5 eş zamanlı pozisyon
- Günlük %10 kayıp limiti
- Kasanın max %50'si riske atılabilir
- Coin bazlı blacklist (3 art arda kayıp → 32 mum devre dışı)
- Hard stop loss %7

## [v1.3.0] - 2026-02-12

### 🚀 Yeni Özellikler

#### 💰 Dinamik Marjin Portföy Simülatörü (PortfolioSimulator)

- **Dinamik Sermaye Aktarımı:** TP1/TP2 sonrası serbest kalan marjin + kâr otomatik olarak cüzdana geri aktarılıyor ve yeni pozisyonlarda kullanılabiliyor.
- **Kronolojik Birleşik Simülasyon:** Tüm coinler artık tek bir cüzdan üzerinden kronolojik sırada simüle ediliyor (gerçek trading koşullarına yakın).
- **Olay Tabanlı Mimari:** OPEN/CLOSE event timeline ile modüler ve genişletilebilir yapı.
- **Portföy Drawdown İzleme:** Gerçek portföy değeri üzerinden max drawdown hesaplanıyor (sadece bakiye değil, açık pozisyonların marjinini de dahil ediyor).

#### 🛡️ Strateji İyileştirmeleri

- **Coin Bazlı Dinamik Blacklist:** Art arda 3+ kayıp veren coin'ler 32 mum (~8 saat) boyunca otomatik olarak devre dışı bırakılıyor.
- **Yapay Win Rate Kaldırıldı:** Eski sabit `win_rate` hesabı yerine doğrudan `MIN_REASONS` (minimum 4 farklı teknik sinyal) kontrolü ile daha temiz filtreleme.
- **Blacklist Bug Fix:** Önceki sürümde `consecutive_losses` sayacı 2'de sıfırlandığı için 3+ blacklist hiçbir zaman tetiklenmiyordu — düzeltildi.

### 🧹 Teknik Temizlik

- **Ölü Kod Temizliği:** `return trades` sonrası erişilemeyen duplikat DÖNEM SONU bloğu silindi (14 satır).
- **Excel Uyumluluğu:** CSV çıktılarında ondalık ayracı virgüle çevrilerek Türkçe Excel ile uyum sağlandı.
- **Kronolojik CSV:** `backtest_positions.csv` artık entry_time'a göre sıralı.

### 📊 Backtest Sonuçları (1 Aylık Test: 24 Ağu - 24 Eyl 2025)

| Metrik | Önceki (v1.2) | Yeni (v1.3) | Değişim |
|--------|---------------|-------------|---------|
| Win Rate | %54.8 | %55.2 | ✅ +0.4% |
| Final Bakiye | $2,531 | ~$2,870 | ✅ +$339 |
| Monte Carlo Medyan | $2,527 | $2,698 | ✅ +$171 |
| Max Drawdown (MC) | %46.8 | %44.2 | ✅ -2.6% |
| İflas Riski | %0.00 | %0.00 | ✅ Sabit |

---

## [v1.2.0] - 2026-02-11

### 🚀 Yeni Özellikler

#### Yüksek Performanslı Backtest Motoru (X-Engine)

- **Paralel İşlem (Multiprocessing):** CPU çekirdeklernin (28 çekirdek) tamamını kullanarak backtest süresini %90 oranında azalttı (30 sn -> 3.5 sn).
- **Vektörize Hesaplama (Numpy):** Pandas döngüleri yerine Numpy array operasyonları ile mumu işleme hızı "ışık hızına" çıkarıldı.
- **Monte Carlo Doğrulama:** Stratejinin başarısının şans mı yoksa matematiksel bir güç mü olduğunu test eden simülasyon motoru eklendi:
  - **Bootstrap Resampling:** İşlemleri yerine koyarak seçme yöntemiyle binlerce farklı kârlılık senaryosu üretimi.
  - **İflas Riski (Risk of Ruin) Analizi:** Stratejinin sermayeyi sıfırlama ihtimali hesaplandı.

#### Strateji Optimizasyonu & Risk Yönetimi (v5)

- **Smart Breakeven (BE):** TP1 gerçekleştikten sonra stop loss'un anında giriş fiyatına çekilmesi sağlandı (Kârdaki işlemin zarara dönme riskine son).
- **Overextension Filter (SMA50 Distance):** Fiyatın SMA50'den %3-4 yukarıda olduğu "aşırı şişmiş" durumlar için +30 puanlık bonus eklenerek zirve yakalama kabiliyeti artırıldı.
- **TP1 Dağılımı:** TP1 kapatma oranı %40 olarak optimize edildi (BE ile birleşince risk/kazanç oranı dengelendi).
- **Toxic Metric Neutralization:** Win rate'i yüksek olmasına rağmen PnL'i düşüren EMA ve MACD trend takibi skorları nötrlendi (Bot artık "dibe vuruş" shortlarından kaçınıyor).

### 📊 Backtest & Validasyon Sonuçları (v5)

#### 90 Günlük Stabilite Testi (Kasım 2025 - Şubat 2026)

| Metrik | Değer |
|--------|-------|
| Toplam İşlem | 1595 |
| Win Rate | 54.4% |
| **Risk/Reward** | **1:0.89** (İyileştirildi) |
| **Final Kâr** | **+%290 ($3,900)** |

#### 🎲 Monte Carlo Risk Analizi (5000 Simülasyon)

| Metrik | Değer |
|--------|-------|
| Ortalama Max Drawdown | %25.7 |
| **İflas Riski (Ruin)** | **%0.00** |
| Güven Endeksi | ✅ **SON DERECE SAĞLAM** |

---

## [v1.1.0] - 2026-02-10

### 🚀 Yeni Özellikler

#### Backtest & Strateji Optimizasyonu (Smart Bull Protection)

- **backtest_csv.py** - "Akıllı Boğa Koruması" entegre edildi:
  - **Smart Bull Filter:** Fiyat SMA 50 üzerindeyken daha seçici (Score +10) ve RSI eğimi (yorulma belirtisi) kontrolü.
  - **MACD Bonus:** Boğa bölgesinde sadece MACD onayı varsa ek puan verilerek trend tersi işlemler filtrelendi.
  - **Hard Stop Loss:** Tekil işlemlerde maksimum kayıp %7.0 ile sınırlandırıldı (PIPPIN/RIVER gibi coinlerin hesabı patlatması engellendi).
  - **Circuit Breaker (Devre Kesici):** Bir coin'de 2 kez üst üste stop olunursa, o coin 4 saat (16 mum) boyunca bloklanır.
  - **Metrik Analiz Raporu:** Hangi indikatörün (RSI, MACD, BB vb.) toplam kâr/zarara ne kadar etki ettiğini gösteren detaylı tablo eklendi.

#### Veri Yönetimi & Ölçeklendirme

- **veri_cek.py** - Geliştirilmiş Geçmiş Veri Çekici:
  - **90 Günlük Arşiv:** Veri çekme kapasitesi 30 günden 90 güne çıkarıldı.
  - **Paging Mekanizması:** Bybit'ten parça parça (1000'er mum) veri çekerek geçmişe dönük sınırsız veri indirme imkanı sağlandı.
  - **İlk 100 Coin:** Hacme göre ilk 100 coin için tam kapsamlı veri seti oluşturuldu.

### 📈 Strateji İyileştirmeleri (v3 → v4)

| Özellik | Eski (v3) | Yeni (v4) | Amaç |
|-------|-------|-------|-------|
| MACD İndeksi | Yanlış (Histogram) | Doğru (Signal Line) | Sinyal doğruluğunu artırmak |
| Max Zarar | Sınırsız (ATR tabanlı) | **Max %7.0 (Hard Stop)** | Hesabı korumak |
| Boğa Koruması | Yok | Var (SMA 50 + RSI Slope) | Pump sırasında stop olmayı engellemek |
| Soğuma Süresi | Sabit 8 mum | Dinamik (Loss sonrası 16 mum) | İnatlaşmayı önlemek |
| Kaldıraç | 10x | 5x | Risk yönetimi |

### 📊 Backtest Sonuçları (Güncel)

#### 90 Günlük Karma Test (Kasım 2025 - Şubat 2026)

| Metrik | Değer |
|--------|-------|
| Toplam İşlem | 2485 |
| Win Rate | 54.8% |
| Başlangıç | $1,000 |
| Final | $3,572 |
| **Toplam Kar** | **+$2,572 (+%257)** |

#### ⚡ Pump Dönemi Direnci (BTC 63k -> 71k Testi)

- **Korumasız Strateji:** -%29.74 zarar
- **v4 Korumalı Strateji:** **-%8.99 zarar** (Kalkanlar sayesinde ayakta kalındı)

### � Çözülen Sorunlar

- **MACD Bug:** Signal Line yerine Histogram'ın okunması hatası giderildi.
- **Unicode Error:** Terminal çıktılarını bozan emoji/karakter kodlama sorunları optimize edildi.
- **Paging Issue:** Bybit API'den sadece son 1000 mumu çekebilme sınırı paging ile aşıldı.

---

## [v1.0.0] - 2026-02-09

### 🚀 Yeni Özellikler

#### Trading Bot Sistemleri

- **short_bot.py** - SHORT sinyal trading botu oluşturuldu
- **ultra_short_bot.py** - Geliştirilmiş ultra short bot
- **scan_50_100.py** - Coin tarama scripti

#### Backtest Sistemleri

- **backtest_csv.py** - Hızlı CSV tabanlı backtest (v3)
- **veri_cek.py** - OHLCV veri çekme scripti

### 📁 Proje Yapısı (v1.1)

```
murat/
├── backtest_csv.py      # Akıllı Boğa Korumalı Backtest ⭐
├── veri_cek.py          # 90 Günlük Paging Destekli Veri Çekici ⭐
├── backtest_data/       # 100 coin / 90 günlük CSV verisi
└── ...
```

---

## Sonraki Adımlar (Planlar)

- [x] İlk 100 coin için 90 günlük veri çekimi
- [ ] LONG sinyal stratejisi ekleme ve SHORT ile hibrit çalıştırma
- [ ] Kalıcı veri tabanı (SQLite/PostgreSQL) entegrasyonu
- [ ] Canlı trading modu (Paper Trading sonrası)
- [ ] Web Dashboard

---
*Son güncelleme: 2026-02-11*
