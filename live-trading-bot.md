# 🤖 Canlı Trading Bot - İmplementasyon Planı

## Hedef

Backtest motorundaki stratejiyi (v1.3.0) canlı Binance Futures paper trading'e dönüştürmek.

## Mimari (Modüler)

```
bugra-bot/
├── config.py           # Tüm ayarlar (.env + defaults)
├── strategy.py         # Strateji mantığı (backtest'ten alınan scoring)
├── exchange.py         # CCXT Binance Futures connector
├── scanner.py          # Top 100 coin tarayıcı (sürekli döngü)
├── trader.py           # İşlem yöneticisi (SL/TP/Trailing)
├── portfolio.py        # Portföy + risk yönetimi
├── notifier.py         # Telegram bildirim servisi
├── bot.py              # Ana bot döngüsü (orchestrator)
├── .env                # API keys (gitignore'da)
├── backtest_csv_v2.py  # Mevcut backtest motoru (dokunulmaz)
└── requirements.txt    # Bağımlılıklar
```

## Faz 1: Temel Modüller (Bugün)

1. `config.py` - Ayarlar + .env
2. `exchange.py` - CCXT Binance Futures (paper mode)
3. `strategy.py` - Sinyal motoru (backtest'ten taşıma)
4. `scanner.py` - Top 100 coin tarama
5. `trader.py` - İşlem açma/kapama (TP/SL)
6. `portfolio.py` - Portföy yönetimi
7. `notifier.py` - Telegram bildirim
8. `bot.py` - Ana döngü

## Risk Yönetimi Ayarları

- MAX_RISK_PCT: Kasanın max %'si riske atılabilir (default: 50)
- MAX_CONCURRENT: Max eş zamanlı pozisyon (default: 5)
- DAILY_LOSS_LIMIT_PCT: Günlük max kayıp limiti (default: 10)
