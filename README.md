# 🚀 Bugra Bot - High-Performance Crypto Backtesting Engine

Bugra Bot, kripto para piyasaları için optimize edilmiş, yüksek hızlı (X-Engine) ve paralel işlem destekli bir backtest motorudur. Proje, tarihsel veriler üzerinde stratejileri test etmek için özel bir "Discrete Scoring" (Kesikli Puanlama) sistemi ve istatistiksel doğrulama için Monte Carlo simülasyonları kullanır.

## 🌟 Öne Çıkan Özellikler

* **⚡ X-Engine (Işık Hızında Analiz)**: NumPy vektörizasyonu ve Python `ProcessPoolExecutor` ile çok çekirdekli (Multiprocessing) işlem yapar. 100 coin için 90 günlük veriyi saniyeler içinde analiz eder.
* **📊 Çift Yönlü Strateji (v5)**: Hem LONG hem de SHORT pozisyonları için ayrı ayrı optimize edilmiş, birbirinden bağımsız çalışan puanlama motorları.
* **🎯 Kesikli Puanlama (Discrete Scoring)**: 7+ teknik göstergenin (RSI, MACD, BB, ADX, DI, StochRSI, MFI) birleşimiyle 0-150 arası "Güven Puanı" oluşturur.
* **🎲 Monte Carlo Validasyonu**: Strateji başarısını 5000+ simülasyonla test eder. Bootstrap Resampling yöntemiyle "İflas Riski" (Risk of Ruin) ve en kötü senaryo analizlerini raporlar.
* **🛡️ Akıllı Risk Yönetimi**:
  * **Smart Breakeven (BE)**: TP1 sonrası zarar riskini sıfırlama.
  * **Hard Stop Loss**: %7.0 sabit sınır (Pump/Dump koruması).
  * **Circuit Breaker**: Ardışık zararlarda ilgili coini geçici bloklama.
  * **Partial TP**: 3 kademeli kar alım (%40 - %30 - %30).

## 📂 Proje Yapısı

* `backtest_csv.py`: Güncel geliştirme ve optimizasyon motoru.
* `backtest_csv_v2_discrete_backup.py`: **Altın Versiyon**. En kararlı ve kârlı strateji mantığını içeren referans dosya.
* `veri_cek.py`: Binance/Bybit üzerinden 90+ günlük OHLCV verisini (15m) çeken paging destekli script.
* `CHANGELOG.md`: Sürüm notları ve metrik iyileştirme tarihçesi.

## 🛠️ Kurulum

```bash
# Repo'yu klonlayın
git clone <repo-url>
cd bugra-bot

# Gerekli kütüphaneleri yükleyin
pip install pandas pandas_ta numpy
```

## 🚀 Kullanım

### 1. Veri Hazırlama

Analiz edilecek coinlerin listesini ve verilerini güncellemek için:

```bash
python veri_cek.py
```

### 2. Analiz Başlatma

Parametreleri `backtest_csv.py` içinden (Tarih, Side, Leverage) ayarlayıp çalıştırın:

```bash
python backtest_csv.py
```

## 📈 Strateji Mimarisi

### SHORT Puanlama (Örnek)

| Metrik | Puan | Kriter |
| :--- | :--- | :--- |
| **Overextension** | +25 | Fiyat > SMA50 %4 mesafe (Zirve yakalama) |
| **RSI** | +30 | RSI > 80 (Aşırı şişme) |
| **MACD-** | +5 | Bearish Cross / Sinyal altı |
| **Bollinger** | +25 | Üst bant aşımı (>0.95) |

### LONG Puanlama (Örnek)

| Metrik | Puan | Kriter |
| :--- | :--- | :--- |
| **RSI Bounce** | +40 | RSI < 30 (Dip dönüşü) |
| **MACD+** | +40 | MACD Bullish Cross |
| **Trend Bonus** | +15 | Fiyat > SMA50 (Boğa rejimi) |

## 📊 İstatistiksel Güvenilirlik

Proje, her backtest sonunda detaylı bir "Metrik Analiz Tablosu" sunar. Hangi indikatörün (RSI, MFI vb.) stratejiye kâr mı yoksa zarar mı getirdiğini görerek her coin için ayrı optimizasyon yapmanıza olanak tanır.

---
*⚠️ **Feragatname**: Bu yazılım kripto para piyasalarında tarihsel verileri analiz etmek için geliştirilmiştir. Gerçek para ile işlem yapmadan önce tüm riskleri değerlendirmeli ve projenin yatırım tavsiyesi olmadığını bilmelisiniz.*
