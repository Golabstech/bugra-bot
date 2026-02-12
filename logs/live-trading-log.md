PS C:\Users\murat\bugra-bot> python run.py
16:30:26 | bot        | INFO  | ============================================================
16:30:26 | bot        | INFO  | 🤖 BUGRA-BOT v1.3.0 — Canlı Trading Motoru
16:30:26 | bot        | INFO  | ============================================================
16:30:26 | exchange   | INFO  | 🧪 DEMO TRADING (Mock) modu aktif
16:30:32 | bot        | INFO  | 💰 Bakiye: $4987.97 (Free: $3704.96)
16:30:32 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:30:32 | bot        | INFO  |
🔄 Döngü #1 başlıyor...
16:30:32 | scanner    | INFO  | 🔄 Top 100 coin listesi yenileniyor...
16:30:34 | scanner    | INFO  | ✅ 100 coin yüklendi
16:30:52 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 120 | ADX(44)+DI-, SMA50_OE(20.2%), RSI(79), BB(110%), Stoch(100)
16:30:58 | strategy   | INFO  | 🎯 SİNYAL: PUFFER/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(6.0%), RSI(78), BB(117%), Stoch(100), MFI(92)
16:31:07 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 115 | SMA50_OE(9.4%), RSI(81), BB(114%), Stoch(100), MFI(89)
16:31:10 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: TOSHI/USDT:USDT skor:120)
16:31:11 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:31:12 | exchange   | INFO  | ⚙️ TOSHI/USDT:USDT kaldıraç: 5x
16:31:12 | exchange   | INFO  | 📉 SHORT açıldı: TOSHI/USDT:USDT | Miktar: 7122174.8078
16:31:12 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position TOSHI/USDT:USDT SHORT @ 0.0002588 | Remaining: 100%>
16:31:13 | exchange   | INFO  | 🛑 SL ayarlandı: TOSHI/USDT:USDT @ 0.000275
16:31:13 | exchange   | INFO  | 🎯 TP ayarlandı: TOSHI/USDT:USDT @ 0.000233
16:31:13 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:31:13 | trader     | INFO  | ✅ TOSHI/USDT:USDT SHORT açıldı @ 0.0002588 | Margin: $370.5
16:31:15 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
16:31:16 | exchange   | INFO  | ⚙️ PUFFER/USDT:USDT kaldıraç: 5x
16:31:17 | exchange   | INFO  | 📉 SHORT açıldı: PUFFER/USDT:USDT | Miktar: 47296.7339
16:31:17 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position PUFFER/USDT:USDT SHORT @ 0.0352 | Remaining: 100%>
16:31:17 | exchange   | INFO  | 🛑 SL ayarlandı: PUFFER/USDT:USDT @ 0.036089
16:31:17 | exchange   | INFO  | 🎯 TP ayarlandı: PUFFER/USDT:USDT @ 0.033795
16:31:18 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
16:31:18 | trader     | INFO  | ✅ PUFFER/USDT:USDT SHORT açıldı @ 0.0352 | Margin: $333.63
16:31:20 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:31:20 | exchange   | INFO  | ⚙️ MOODENG/USDT:USDT kaldıraç: 5x
16:31:21 | exchange   | INFO  | 📉 SHORT açıldı: MOODENG/USDT:USDT | Miktar: 30208.6849
16:31:21 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position MOODENG/USDT:USDT SHORT @ 0.0497 | Remaining: 100%>
16:31:21 | exchange   | INFO  | 🛑 SL ayarlandı: MOODENG/USDT:USDT @ 0.051762
16:31:22 | exchange   | INFO  | 🎯 TP ayarlandı: MOODENG/USDT:USDT @ 0.046016
16:31:22 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:31:22 | trader     | INFO  | ✅ MOODENG/USDT:USDT SHORT açıldı @ 0.0497 | Margin: $300.33
16:31:23 | bot        | INFO  | 📊 Bakiye: $4937.57 | Açık: 3 | Günlük PnL: $+0.00 | W/L: 0/0
16:31:23 | bot        | INFO  | ⏳ 60s bekleniyor...
16:32:23 | bot        | INFO  |
🔄 Döngü #2 başlıyor...
16:32:43 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 120 | ADX(44)+DI-, SMA50_OE(19.6%), RSI(77), BB(108%), Stoch(98)
16:32:50 | strategy   | INFO  | 🎯 SİNYAL: PUFFER/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.2%), RSI(68), BB(102%), Stoch(90), MFI(92)
16:32:50 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(4.0%), RSI(66), BB(95%)
16:32:59 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 115 | SMA50_OE(11.6%), RSI(84), BB(124%), Stoch(100), MFI(90)
16:33:02 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: TOSHI/USDT:USDT skor:120)
16:33:02 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
16:33:03 | exchange   | INFO  | ⚙️ H/USDT:USDT kaldıraç: 5x
16:33:04 | exchange   | INFO  | 📉 SHORT açıldı: H/USDT:USDT | Miktar: 7288.9295
16:33:04 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position H/USDT:USDT SHORT @ 0.16435 | Remaining: 100%>
16:33:04 | exchange   | INFO  | 🛑 SL ayarlandı: H/USDT:USDT @ 0.167888
16:33:05 | exchange   | INFO  | 🎯 TP ayarlandı: H/USDT:USDT @ 0.158346
16:33:05 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
16:33:05 | trader     | INFO  | ✅ H/USDT:USDT SHORT açıldı @ 0.16435 | Margin: $239.78
16:33:06 | bot        | INFO  | 📊 Bakiye: $4929.24 | Açık: 4 | Günlük PnL: $+0.00 | W/L: 0/0
16:33:06 | bot        | INFO  | ⏳ 60s bekleniyor...
16:34:06 | bot        | INFO  |
🔄 Döngü #3 başlıyor...
16:34:25 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 120 | ADX(44)+DI-, SMA50_OE(19.6%), RSI(77), BB(108%), Stoch(98)
16:34:32 | strategy   | INFO  | 🎯 SİNYAL: PUFFER/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.3%), RSI(68), BB(102%), Stoch(91), MFI(93)
16:34:32 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(4.0%), RSI(66), BB(95%)
16:34:37 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.8%), RSI(74), BB(107%), Stoch(100), MFI(82)
16:34:43 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: TOSHI/USDT:USDT skor:120)
16:34:44 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:34:45 | exchange   | INFO  | ⚙️ Q/USDT:USDT kaldıraç: 5x
16:34:45 | exchange   | INFO  | 📉 SHORT açıldı: Q/USDT:USDT | Miktar: 62359.7883
16:34:45 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position Q/USDT:USDT SHORT @ 0.019528 | Remaining: 100%>
16:34:46 | exchange   | INFO  | 🛑 SL ayarlandı: Q/USDT:USDT @ 0.019924
16:34:46 | exchange   | INFO  | 🎯 TP ayarlandı: Q/USDT:USDT @ 0.018706
16:34:46 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:34:46 | trader     | INFO  | ✅ Q/USDT:USDT SHORT açıldı @ 0.019528 | Margin: $243.07
16:34:48 | bot        | INFO  | 📊 Bakiye: $4945.05 | Açık: 5 | Günlük PnL: $+0.00 | W/L: 0/0
16:34:48 | bot        | INFO  | ⏳ 60s bekleniyor...
16:35:48 | bot        | INFO  |
🔄 Döngü #4 başlıyor...
16:35:50 | exchange   | INFO  | 🗑️ Tüm emirler iptal edildi: MOODENG/USDT:USDT
16:35:50 | exchange   | ERROR | ❌ Pozisyon kapatılamadı MOODENG/USDT:USDT: binance {"code":-2022,"msg":"ReduceOnly Order is rejected."}
16:35:50 | portfolio  | INFO  | 🗑️ Pozisyon silindi: MOODENG/USDT:USDT | STOP LOSS | PnL: $-12.99
16:35:50 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:35:50 | trader     | INFO  | ❌ MOODENG/USDT:USDT kapatıldı: STOP LOSS | PnL: -4.33% ($-12.99)
16:36:08 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 120 | ADX(44)+DI-, SMA50_OE(19.1%), RSI(76), BB(107%), Stoch(96)
16:36:14 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(4.2%), RSI(66), BB(99%)
16:36:19 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(5.0%), RSI(75), BB(110%), Stoch(100), MFI(82)
16:36:25 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: TOSHI/USDT:USDT skor:120)
16:36:26 | bot        | INFO  | 📊 Bakiye: $4956.96 | Açık: 4 | Günlük PnL: $-12.99 | W/L: 0/1
16:36:26 | bot        | INFO  | ⏳ 60s bekleniyor...
16:41:24 | bot        | INFO  |
🔄 Döngü #5 başlıyor...
16:41:34 | exchange   | ERROR | ❌ Ticker alınamadı TOSHI/USDT:USDT: binance GET https://demo-fapi.binance.com/fapi/v1/ticker/24hr?symbol=TOSHIUSDT
16:41:54 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 120 | ADX(44)+DI-, SMA50_OE(18.7%), RSI(75), BB(106%), Stoch(95)
16:42:01 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(4.6%), RSI(68), BB(106%)
16:42:05 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.2%), RSI(72), BB(101%), Stoch(100), MFI(83)
16:42:12 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: TOSHI/USDT:USDT skor:120)
16:42:12 | bot        | INFO  | 📊 Bakiye: $4993.32 | Açık: 4 | Günlük PnL: $-12.99 | W/L: 0/1
16:42:12 | bot        | INFO  | ⏳ 60s bekleniyor...
16:43:12 | bot        | INFO  |
🔄 Döngü #6 başlıyor...
16:43:25 | strategy   | INFO  | 🎯 SİNYAL: RIVER/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(12.8%), RSI(72), BB(96%), Stoch(90)
16:43:31 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 135 | ADX(44)+DI-, SMA50_OE(18.2%), RSI(73), BB(105%), Stoch(93), MFI(80)
16:43:38 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(4.6%), RSI(68), BB(106%)
16:43:43 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.3%), RSI(73), BB(101%), Stoch(100), MFI(83)
16:43:50 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: TOSHI/USDT:USDT skor:135)
16:43:50 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
16:43:51 | exchange   | INFO  | ⚙️ RIVER/USDT:USDT kaldıraç: 5x
16:43:52 | exchange   | INFO  | 📉 SHORT açıldı: RIVER/USDT:USDT | Miktar: 64.1067
16:43:52 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position RIVER/USDT:USDT SHORT @ 19.194585 | Remaining: 100%>
16:43:52 | exchange   | INFO  | 🛑 SL ayarlandı: RIVER/USDT:USDT @ 20.394038
16:43:52 | exchange   | INFO  | 🎯 TP ayarlandı: RIVER/USDT:USDT @ 17.232732
16:43:53 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
16:43:53 | trader     | INFO  | ✅ RIVER/USDT:USDT SHORT açıldı @ 19.194585 | Margin: $247.0
16:43:54 | bot        | INFO  | 📊 Bakiye: $4977.19 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:43:54 | bot        | INFO  | ⏳ 60s bekleniyor...
16:44:54 | bot        | INFO  |
🔄 Döngü #7 başlıyor...
16:45:14 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 135 | ADX(44)+DI-, SMA50_OE(18.2%), RSI(73), BB(105%), Stoch(93), MFI(80)
16:45:21 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(4.9%), RSI(69), BB(110%)
16:45:26 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.4%), RSI(73), BB(102%), Stoch(100), MFI(83)
16:45:32 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: TOSHI/USDT:USDT skor:135)
16:45:33 | bot        | INFO  | 📊 Bakiye: $4932.27 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:45:33 | bot        | INFO  | ⏳ 60s bekleniyor...
16:46:33 | bot        | INFO  |
🔄 Döngü #8 başlıyor...
16:46:34 | exchange   | INFO  | ✅ Pozisyon kapatıldı: PUFFER/USDT:USDT | 18918.6936
16:46:35 | exchange   | INFO  | 🗑️ Tüm emirler iptal edildi: PUFFER/USDT:USDT
16:46:35 | exchange   | INFO  | 🛑 SL ayarlandı: PUFFER/USDT:USDT @ 0.0352
16:46:35 | exchange   | INFO  | 🎯 TP ayarlandı: PUFFER/USDT:USDT @ 0.032976
16:46:36 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:46:36 | trader     | INFO  | 🎯 TP1 HIT: PUFFER/USDT:USDT @ 0.03377
16:46:54 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 125 | ADX(46)+DI-, SMA50_OE(17.0%), RSI(72), BB(95%), Stoch(85), MFI(86)
16:47:03 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(4.7%), RSI(69), BB(101%)
16:47:08 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.9%), RSI(75), BB(101%), Stoch(100), MFI(86)
16:47:12 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 135 | ADX(50)+DI-, SMA50_OE(14.2%), RSI(78), BB(108%), Stoch(89), MFI(93)
16:47:16 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: MOODENG/USDT:USDT skor:135)
16:47:16 | bot        | INFO  | 📊 Bakiye: $4964.92 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:47:16 | bot        | INFO  | ⏳ 60s bekleniyor...
16:48:16 | bot        | INFO  |
🔄 Döngü #9 başlıyor...
16:48:37 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 125 | ADX(46)+DI-, SMA50_OE(16.8%), RSI(71), BB(94%), Stoch(84), MFI(86)
16:48:45 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(5.3%), RSI(71), BB(109%)
16:48:50 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(5.0%), RSI(76), BB(102%), Stoch(100), MFI(86)
16:48:51 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.7%), RSI(70), BB(127%), Stoch(100)
16:48:54 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 135 | ADX(50)+DI-, SMA50_OE(14.5%), RSI(79), BB(109%), Stoch(90), MFI(93)
16:48:56 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: MOODENG/USDT:USDT skor:135)
16:48:57 | bot        | INFO  | 📊 Bakiye: $4981.30 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:48:57 | bot        | INFO  | ⏳ 60s bekleniyor...
16:49:57 | bot        | INFO  |
🔄 Döngü #10 başlıyor...
16:50:19 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 105 | SMA50_OE(18.9%), RSI(75), BB(100%), Stoch(89), MFI(87)
16:50:25 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(4.8%), RSI(70), BB(102%)
16:50:29 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | ADX(41)+DI-, SMA50_OE(10.0%), RSI(75), BB(95%)
16:50:30 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(5.0%), RSI(76), BB(102%), Stoch(100), MFI(86)
16:50:31 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.7%), RSI(70), BB(127%), Stoch(100)
16:50:34 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 145 | ADX(50)+DI-, SMA50_OE(14.9%), RSI(80), BB(110%), Stoch(91), MFI(94)
16:50:36 | scanner    | INFO  | 🎯 6 sinyal bulundu (top: MOODENG/USDT:USDT skor:145)
16:50:37 | bot        | INFO  | 📊 Bakiye: $4936.31 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:50:37 | bot        | INFO  | ⏳ 60s bekleniyor...
16:51:37 | bot        | INFO  |
🔄 Döngü #11 başlıyor...
16:51:56 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 105 | SMA50_OE(17.8%), RSI(74), BB(97%), Stoch(88), MFI(84)
16:52:03 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(4.9%), RSI(70), BB(104%)
16:52:06 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | ADX(41)+DI-, SMA50_OE(10.1%), RSI(76), BB(97%)
16:52:08 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(5.0%), RSI(76), BB(102%), Stoch(100), MFI(86)
16:52:08 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.9%), RSI(70), BB(128%), Stoch(100)
16:52:12 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 135 | ADX(50)+DI-, SMA50_OE(14.2%), RSI(78), BB(108%), Stoch(89), MFI(94)
16:52:14 | scanner    | INFO  | 🎯 6 sinyal bulundu (top: MOODENG/USDT:USDT skor:135)
16:52:14 | bot        | INFO  | 📊 Bakiye: $4982.23 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:52:14 | bot        | INFO  | ⏳ 60s bekleniyor...
16:53:14 | bot        | INFO  |
🔄 Döngü #12 başlıyor...
16:53:40 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(4.9%), RSI(70), BB(104%)
16:53:45 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(5.0%), RSI(76), BB(102%), Stoch(100), MFI(86)
16:53:45 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.1%), RSI(71), BB(130%), Stoch(100)
16:53:48 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 105 | SMA50_OE(14.1%), RSI(77), BB(108%), Stoch(88), MFI(94)
16:53:51 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: Q/USDT:USDT skor:120)
16:53:51 | bot        | INFO  | 📊 Bakiye: $4985.15 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:53:51 | bot        | INFO  | ⏳ 60s bekleniyor...
16:54:51 | bot        | INFO  |
🔄 Döngü #13 başlıyor...
16:55:17 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(5.6%), RSI(72), BB(112%)
16:55:21 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | DI->DI+, SMA50_OE(4.0%), RSI(70), BB(92%), Stoch(95), MFI(87)
16:55:22 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.8%), RSI(73), BB(135%), Stoch(100)
16:55:25 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 115 | SMA50_OE(14.9%), RSI(80), BB(110%), Stoch(91), MFI(94)
16:55:28 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: MOODENG/USDT:USDT skor:115)
16:55:29 | bot        | INFO  | 📊 Bakiye: $4947.40 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:55:29 | bot        | INFO  | ⏳ 60s bekleniyor...
16:56:29 | bot        | INFO  |
🔄 Döngü #14 başlıyor...
16:56:49 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 105 | SMA50_OE(17.5%), RSI(73), BB(96%), Stoch(87), MFI(83)
16:56:55 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(5.7%), RSI(73), BB(114%)
16:57:00 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | DI->DI+, SMA50_OE(4.1%), RSI(70), BB(92%), Stoch(96), MFI(87)
16:57:00 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.8%), RSI(73), BB(135%), Stoch(100)
16:57:04 | strategy   | INFO  | 🎯 SİNYAL: MOODENG/USDT:USDT SHORT | Skor: 105 | SMA50_OE(14.2%), RSI(78), BB(108%), Stoch(89), MFI(94)
16:57:06 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: Q/USDT:USDT skor:110)
16:57:06 | bot        | INFO  | 📊 Bakiye: $4963.89 | Açık: 5 | Günlük PnL: $-12.99 | W/L: 0/1
16:57:06 | bot        | INFO  | ⏳ 60s bekleniyor...
16:58:06 | bot        | INFO  |
🔄 Döngü #15 başlıyor...
16:58:08 | exchange   | INFO  | 🗑️ Tüm emirler iptal edildi: H/USDT:USDT
16:58:09 | exchange   | ERROR | ❌ Pozisyon kapatılamadı H/USDT:USDT: binance {"code":-2022,"msg":"ReduceOnly Order is rejected."}
16:58:09 | portfolio  | INFO  | 🗑️ Pozisyon silindi: H/USDT:USDT | STOP LOSS | PnL: $-5.49
16:58:09 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
16:58:09 | trader     | INFO  | ❌ H/USDT:USDT kapatıldı: STOP LOSS | PnL: -2.29% ($-5.49)
16:58:33 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(6.1%), RSI(74), BB(118%)
16:58:38 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | DI->DI+, SMA50_OE(4.1%), RSI(70), BB(92%), Stoch(95), MFI(87)
16:58:38 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.6%), RSI(69), BB(125%), Stoch(100)
16:58:44 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: Q/USDT:USDT skor:110)
16:58:45 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:58:46 | exchange   | INFO  | ⚙️ GPS/USDT:USDT kaldıraç: 5x
16:58:46 | exchange   | INFO  | 📉 SHORT açıldı: GPS/USDT:USDT | Miktar: 128134.9013
16:58:46 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position GPS/USDT:USDT SHORT @ 0.0106 | Remaining: 100%>
16:58:47 | exchange   | INFO  | 🛑 SL ayarlandı: GPS/USDT:USDT @ 0.010888
16:58:47 | exchange   | INFO  | 🎯 TP ayarlandı: GPS/USDT:USDT @ 0.010157
16:58:47 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
16:58:47 | trader     | INFO  | ✅ GPS/USDT:USDT SHORT açıldı @ 0.0106 | Margin: $272.34
16:58:49 | bot        | INFO  | 📊 Bakiye: $4953.35 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
16:58:49 | bot        | INFO  | ⏳ 60s bekleniyor...
16:59:49 | bot        | INFO  |
🔄 Döngü #16 başlıyor...
17:00:02 | strategy   | INFO  | 🎯 SİNYAL: RIVER/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(13.8%), RSI(74), BB(95%), Stoch(92)
17:00:15 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(6.1%), RSI(74), BB(118%)
17:00:20 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | DI->DI+, SMA50_OE(4.1%), RSI(71), BB(93%), Stoch(96), MFI(87)
17:00:21 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.6%), RSI(69), BB(125%), Stoch(100)
17:00:27 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: Q/USDT:USDT skor:110)
17:00:27 | bot        | INFO  | 📊 Bakiye: $4959.08 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:00:27 | bot        | INFO  | ⏳ 60s bekleniyor...
17:01:27 | bot        | INFO  |
🔄 Döngü #17 başlıyor...
17:01:53 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(5.6%), RSI(73), BB(103%), Stoch(93)
17:01:56 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 120 | ADX(42)+DI-, SMA50_OE(9.7%), RSI(75), BB(95%), Stoch(88)
17:01:58 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.3%), RSI(68), BB(110%), Stoch(100)
17:02:04 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: H/USDT:USDT skor:120)
17:02:04 | bot        | INFO  | 📊 Bakiye: $4966.31 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:02:04 | bot        | INFO  | ⏳ 60s bekleniyor...
17:03:04 | bot        | INFO  |
🔄 Döngü #18 başlıyor...
17:03:29 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(5.6%), RSI(72), BB(103%), Stoch(92)
17:03:33 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 120 | ADX(42)+DI-, SMA50_OE(9.7%), RSI(75), BB(96%), Stoch(88)
17:03:34 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.7%), RSI(70), BB(114%), Stoch(100)
17:03:40 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: H/USDT:USDT skor:120)
17:03:40 | bot        | INFO  | 📊 Bakiye: $4995.28 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:03:40 | bot        | INFO  | ⏳ 60s bekleniyor...
17:04:40 | bot        | INFO  |
🔄 Döngü #19 başlıyor...
17:04:46 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(41)+DI-, SMA50_OE(4.2%), RSI(67), BB(120%), Stoch(97)
17:05:07 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(5.8%), RSI(73), BB(105%), Stoch(94)
17:05:11 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 120 | ADX(42)+DI-, SMA50_OE(9.9%), RSI(76), BB(97%), Stoch(88)
17:05:13 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.6%), RSI(69), BB(113%), Stoch(100)
17:05:19 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:05:19 | bot        | INFO  | 📊 Bakiye: $4993.51 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:05:19 | bot        | INFO  | ⏳ 60s bekleniyor...
17:06:19 | bot        | INFO  |
🔄 Döngü #20 başlıyor...
17:06:25 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 105 | ADX(41)+DI-, SMA50_OE(3.7%), RSI(65), BB(114%), Stoch(97)
17:06:46 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(6.0%), RSI(74), BB(107%), Stoch(94)
17:06:49 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 120 | ADX(42)+DI-, SMA50_OE(9.9%), RSI(76), BB(97%), Stoch(88)
17:06:51 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.9%), RSI(70), BB(117%), Stoch(100)
17:06:57 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: H/USDT:USDT skor:120)
17:06:57 | bot        | INFO  | 📊 Bakiye: $5025.23 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:06:57 | bot        | INFO  | ⏳ 60s bekleniyor...
17:07:58 | bot        | INFO  |
🔄 Döngü #21 başlıyor...
17:08:04 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 105 | ADX(41)+DI-, SMA50_OE(3.7%), RSI(65), BB(114%), Stoch(97)
17:08:22 | strategy   | INFO  | 🎯 SİNYAL: MANTA/USDT:USDT SHORT | Skor: 120 | ADX(29)+DI-, SMA50_OE(2.5%), RSI(65), BB(96%), Stoch(89), MFI(89)
17:08:24 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(6.1%), RSI(74), BB(109%), Stoch(94)
17:08:28 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 110 | ADX(42)+DI-, SMA50_OE(9.2%), RSI(73), BB(89%), Stoch(84)
17:08:30 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.3%), RSI(68), BB(110%), Stoch(100)
17:08:36 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: MANTA/USDT:USDT skor:120)
17:08:36 | bot        | INFO  | 📊 Bakiye: $5011.60 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:08:36 | bot        | INFO  | ⏳ 60s bekleniyor...
17:09:36 | bot        | INFO  |
🔄 Döngü #22 başlıyor...
17:10:02 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(6.2%), RSI(75), BB(109%), Stoch(94)
17:10:06 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 110 | ADX(42)+DI-, SMA50_OE(9.2%), RSI(73), BB(89%), Stoch(84)
17:10:07 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.4%), RSI(69), BB(111%), Stoch(100)
17:10:13 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: H/USDT:USDT skor:120)
17:10:13 | bot        | INFO  | 📊 Bakiye: $4982.73 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:10:13 | bot        | INFO  | ⏳ 60s bekleniyor...
17:11:13 | bot        | INFO  |
🔄 Döngü #23 başlıyor...
17:11:39 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(5.9%), RSI(74), BB(106%), Stoch(94)
17:11:44 | strategy   | INFO  | 🎯 SİNYAL: GPS/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(4.7%), RSI(70), BB(115%), Stoch(100), MFI(80)
17:11:50 | scanner    | INFO  | 🎯 2 sinyal bulundu (top: H/USDT:USDT skor:120)
17:11:50 | bot        | INFO  | 📊 Bakiye: $4989.18 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:11:50 | bot        | INFO  | ⏳ 60s bekleniyor...
17:12:50 | bot        | INFO  |
🔄 Döngü #24 başlıyor...
17:13:16 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(6.0%), RSI(74), BB(108%), Stoch(94)
17:13:27 | scanner    | INFO  | 🎯 1 sinyal bulundu (top: H/USDT:USDT skor:120)
17:13:27 | bot        | INFO  | 📊 Bakiye: $4973.34 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:13:27 | bot        | INFO  | ⏳ 60s bekleniyor...
17:14:27 | bot        | INFO  |
🔄 Döngü #25 başlıyor...
17:14:54 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(5.0%), RSI(68), BB(95%), Stoch(85)
17:15:06 | scanner    | INFO  | 🎯 1 sinyal bulundu (top: H/USDT:USDT skor:120)
17:15:06 | bot        | INFO  | 📊 Bakiye: $4946.59 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:15:06 | bot        | INFO  | ⏳ 60s bekleniyor...
17:16:06 | bot        | INFO  |
🔄 Döngü #26 başlıyor...
17:16:45 | scanner    | INFO  | 🔍 Sinyal bulunamadı
17:16:45 | bot        | INFO  | 📊 Bakiye: $4970.11 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:16:45 | bot        | INFO  | ⏳ 60s bekleniyor...
17:17:45 | bot        | INFO  |
🔄 Döngü #27 başlıyor...
17:17:51 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(42)+DI-, SMA50_OE(4.4%), RSI(68), BB(116%), Stoch(98)
17:18:16 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.1%), RSI(69), BB(110%), Stoch(100)
17:18:23 | scanner    | INFO  | 🎯 2 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:18:23 | bot        | INFO  | 📊 Bakiye: $4973.86 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:18:23 | bot        | INFO  | ⏳ 60s bekleniyor...
17:19:23 | bot        | INFO  |
🔄 Döngü #28 başlıyor...
17:19:29 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 105 | ADX(42)+DI-, SMA50_OE(3.9%), RSI(66), BB(108%), Stoch(98)
17:19:53 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 105 | ADX(27)+DI-, SMA50_OE(2.1%), RSI(66), BB(102%), Stoch(98)
17:19:55 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.9%), RSI(71), BB(117%), Stoch(100)
17:20:03 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: CUDIS/USDT:USDT skor:105)
17:20:03 | bot        | INFO  | 📊 Bakiye: $4946.03 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:20:03 | bot        | INFO  | ⏳ 60s bekleniyor...
17:21:03 | bot        | INFO  |
🔄 Döngü #29 başlıyor...
17:21:08 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 105 | ADX(42)+DI-, SMA50_OE(4.0%), RSI(67), BB(110%), Stoch(98)
17:21:30 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(27)+DI-, SMA50_OE(2.7%), RSI(69), BB(111%), Stoch(98), MFI(81)
17:21:34 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.7%), RSI(71), BB(115%), Stoch(100)
17:21:41 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:21:41 | bot        | INFO  | 📊 Bakiye: $4971.62 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:21:41 | bot        | INFO  | ⏳ 60s bekleniyor...
17:22:41 | bot        | INFO  |
🔄 Döngü #30 başlıyor...
17:22:47 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 105 | ADX(42)+DI-, SMA50_OE(4.0%), RSI(67), BB(110%), Stoch(98)
17:23:06 | strategy   | INFO  | 🎯 SİNYAL: MANTA/USDT:USDT SHORT | Skor: 110 | ADX(29)+DI-, SMA50_OE(2.7%), RSI(66), BB(95%), Stoch(97), MFI(88)
17:23:09 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(3.7%), RSI(72), BB(122%), Stoch(98), MFI(84)
17:23:12 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.6%), RSI(68), BB(104%), Stoch(100)
17:23:19 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:23:20 | bot        | INFO  | 📊 Bakiye: $4939.05 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:23:20 | bot        | INFO  | ⏳ 60s bekleniyor...
17:24:20 | bot        | INFO  |
🔄 Döngü #31 başlıyor...
17:24:25 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(42)+DI-, SMA50_OE(4.3%), RSI(68), BB(114%), Stoch(98)
17:24:43 | strategy   | INFO  | 🎯 SİNYAL: MANTA/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(3.0%), RSI(67), BB(100%), Stoch(97), MFI(89)
17:24:46 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(3.6%), RSI(72), BB(121%), Stoch(98), MFI(84)
17:24:49 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.6%), RSI(68), BB(104%), Stoch(100)
17:24:56 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:24:56 | bot        | INFO  | 📊 Bakiye: $4959.08 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:24:56 | bot        | INFO  | ⏳ 60s bekleniyor...
17:25:56 | bot        | INFO  |
🔄 Döngü #32 başlıyor...
17:26:02 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(42)+DI-, SMA50_OE(4.3%), RSI(68), BB(114%), Stoch(98)
17:26:15 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 100 | ADX(45)+DI-, SMA50_OE(19.6%), RSI(72), BB(98%)
17:26:23 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(2.9%), RSI(70), BB(114%), Stoch(98), MFI(85)
17:26:26 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.6%), RSI(68), BB(104%), Stoch(100)
17:26:33 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:26:33 | bot        | INFO  | 📊 Bakiye: $5006.09 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:26:33 | bot        | INFO  | ⏳ 60s bekleniyor...
17:27:33 | bot        | INFO  |
🔄 Döngü #33 başlıyor...
17:27:38 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(43)+DI-, SMA50_OE(7.9%), RSI(77), BB(140%), Stoch(98)
17:27:54 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 100 | ADX(45)+DI-, SMA50_OE(21.1%), RSI(73), BB(102%)
17:28:01 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(2.9%), RSI(70), BB(114%), Stoch(98), MFI(85)
17:28:04 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(4.7%), RSI(68), BB(106%), Stoch(100)
17:28:11 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:28:12 | bot        | INFO  | 📊 Bakiye: $5066.54 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:28:12 | bot        | INFO  | ⏳ 60s bekleniyor...
17:29:12 | bot        | INFO  |
🔄 Döngü #34 başlıyor...
17:29:17 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(43)+DI-, SMA50_OE(5.8%), RSI(72), BB(129%), Stoch(98)
17:29:31 | strategy   | INFO  | 🎯 SİNYAL: TOSHI/USDT:USDT SHORT | Skor: 100 | ADX(45)+DI-, SMA50_OE(21.6%), RSI(73), BB(103%)
17:29:39 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(2.6%), RSI(68), BB(109%), Stoch(98), MFI(85)
17:29:43 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.8%), RSI(71), BB(116%), Stoch(100)
17:29:51 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:29:51 | bot        | INFO  | 📊 Bakiye: $5081.95 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:29:51 | bot        | INFO  | ⏳ 60s bekleniyor...
17:30:51 | bot        | INFO  |
🔄 Döngü #35 başlıyor...
17:30:54 | scanner    | INFO  | 🔄 Top 100 coin listesi yenileniyor...
17:30:56 | scanner    | INFO  | ✅ 100 coin yüklendi
17:31:00 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(43)+DI-, SMA50_OE(4.9%), RSI(70), BB(121%), Stoch(98)
17:31:24 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(2.6%), RSI(68), BB(109%), Stoch(98), MFI(85)
17:31:27 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.8%), RSI(71), BB(116%), Stoch(100)
17:31:35 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:31:36 | bot        | INFO  | 📊 Bakiye: $5047.68 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:31:36 | bot        | INFO  | ⏳ 60s bekleniyor...
17:32:36 | bot        | INFO  |
🔄 Döngü #36 başlıyor...
17:32:41 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.4%), RSI(68), BB(103%), Stoch(97)
17:32:57 | strategy   | INFO  | 🎯 SİNYAL: MANTA/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(3.0%), RSI(67), BB(96%), Stoch(99), MFI(89)
17:33:00 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(2.4%), RSI(67), BB(98%), Stoch(98), MFI(82)
17:33:03 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.2%), RSI(72), BB(109%), Stoch(100)
17:33:11 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:33:11 | bot        | INFO  | 📊 Bakiye: $5033.29 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:33:11 | bot        | INFO  | ⏳ 60s bekleniyor...
17:34:11 | bot        | INFO  |
🔄 Döngü #37 başlıyor...
17:34:16 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.4%), RSI(68), BB(103%), Stoch(97)
17:34:24 | strategy   | INFO  | 🎯 SİNYAL: PIPPIN/USDT:USDT SHORT | Skor: 110 | ADX(30)+DI-, SMA50_OE(7.8%), RSI(68), BB(82%), Stoch(81)
17:34:34 | strategy   | INFO  | 🎯 SİNYAL: MANTA/USDT:USDT SHORT | Skor: 120 | ADX(31)+DI-, SMA50_OE(3.0%), RSI(67), BB(96%), Stoch(99), MFI(90)
17:34:38 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(2.3%), RSI(67), BB(97%), Stoch(98), MFI(82)
17:34:41 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.2%), RSI(73), BB(109%), Stoch(100)
17:34:48 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:34:49 | bot        | INFO  | 📊 Bakiye: $5059.15 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:34:49 | bot        | INFO  | ⏳ 60s bekleniyor...
17:35:49 | bot        | INFO  |
🔄 Döngü #38 başlıyor...
17:35:54 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.4%), RSI(68), BB(103%), Stoch(97)
17:36:14 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(2.3%), RSI(67), BB(97%), Stoch(98), MFI(82)
17:36:17 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.4%), RSI(73), BB(111%), Stoch(100)
17:36:25 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:36:25 | bot        | INFO  | 📊 Bakiye: $5051.42 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:36:25 | bot        | INFO  | ⏳ 60s bekleniyor...
17:37:25 | bot        | INFO  |
🔄 Döngü #39 başlıyor...
17:37:30 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.4%), RSI(68), BB(103%), Stoch(97)
17:37:50 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(2.8%), RSI(69), BB(103%), Stoch(100), MFI(85)
17:37:52 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.6%), RSI(68), BB(102%), Stoch(100)
17:37:54 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.8%), RSI(71), BB(106%), Stoch(98)
17:38:02 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:38:02 | bot        | INFO  | 📊 Bakiye: $5082.61 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:38:02 | bot        | INFO  | ⏳ 60s bekleniyor...
17:39:02 | bot        | INFO  |
🔄 Döngü #40 başlıyor...
17:39:07 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.6%), RSI(69), BB(106%), Stoch(99)
17:39:16 | strategy   | INFO  | 🎯 SİNYAL: PIPPIN/USDT:USDT SHORT | Skor: 110 | ADX(30)+DI-, SMA50_OE(7.8%), RSI(68), BB(83%), Stoch(81)
17:39:28 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(2.7%), RSI(69), BB(103%), Stoch(100), MFI(85)
17:39:30 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.4%), RSI(68), BB(100%), Stoch(100)
17:39:32 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.6%), RSI(70), BB(104%), Stoch(97)
17:39:40 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:39:40 | bot        | INFO  | 📊 Bakiye: $5071.92 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:39:40 | bot        | INFO  | ⏳ 60s bekleniyor...
17:40:40 | bot        | INFO  |
🔄 Döngü #41 başlıyor...
17:40:46 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.5%), RSI(68), BB(105%), Stoch(98)
17:41:06 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(3.4%), RSI(72), BB(110%), Stoch(100), MFI(85)
17:41:07 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.5%), RSI(68), BB(101%), Stoch(100)
17:41:09 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.8%), RSI(74), BB(113%), Stoch(100)
17:41:18 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:41:18 | bot        | INFO  | 📊 Bakiye: $5085.92 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:41:18 | bot        | INFO  | ⏳ 60s bekleniyor...
17:42:18 | bot        | INFO  |
🔄 Döngü #42 başlıyor...
17:42:23 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.4%), RSI(67), BB(102%), Stoch(96)
17:42:45 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(3.4%), RSI(72), BB(111%), Stoch(100), MFI(85)
17:42:46 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.4%), RSI(68), BB(100%), Stoch(100)
17:42:48 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(7.0%), RSI(74), BB(115%), Stoch(100)
17:42:56 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:42:56 | bot        | INFO  | 📊 Bakiye: $5096.41 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:42:56 | bot        | INFO  | ⏳ 60s bekleniyor...
17:43:57 | bot        | INFO  |
🔄 Döngü #43 başlıyor...
17:44:02 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(46)+DI-, SMA50_OE(4.2%), RSI(66), BB(100%), Stoch(94)
17:44:12 | strategy   | INFO  | 🎯 SİNYAL: ESP/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(7.5%), RSI(65), BB(102%), Stoch(100)
17:44:24 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(3.4%), RSI(72), BB(110%), Stoch(100), MFI(85)
17:44:25 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.6%), RSI(68), BB(102%), Stoch(100)
17:44:27 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(7.1%), RSI(75), BB(116%), Stoch(100)
17:44:35 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
17:44:35 | bot        | INFO  | 📊 Bakiye: $5113.24 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:44:35 | bot        | INFO  | ⏳ 60s bekleniyor...
17:45:35 | bot        | INFO  |
🔄 Döngü #44 başlıyor...
17:45:40 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 110 | ADX(47)+DI-, SMA50_OE(4.1%), RSI(66), BB(94%), Stoch(89)
17:46:01 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(30)+DI-, SMA50_OE(3.2%), RSI(71), BB(109%), Stoch(100), MFI(85)
17:46:02 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(5.7%), RSI(69), BB(98%), Stoch(100)
17:46:04 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.1%), RSI(71), BB(100%), Stoch(97)
17:46:13 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:46:13 | bot        | INFO  | 📊 Bakiye: $5141.54 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:46:13 | bot        | INFO  | ⏳ 60s bekleniyor...
17:47:13 | bot        | INFO  |
🔄 Döngü #45 başlıyor...
17:47:18 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 110 | ADX(47)+DI-, SMA50_OE(4.1%), RSI(66), BB(94%), Stoch(89)
17:47:40 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(3.0%), RSI(69), BB(97%), Stoch(97), MFI(86)
17:47:41 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.0%), RSI(70), BB(101%), Stoch(100)
17:47:51 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:47:51 | bot        | INFO  | 📊 Bakiye: $5128.64 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:47:51 | bot        | INFO  | ⏳ 60s bekleniyor...
17:48:51 | bot        | INFO  |
🔄 Döngü #46 başlıyor...
17:49:19 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(3.1%), RSI(70), BB(99%), Stoch(99), MFI(86)
17:49:20 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.1%), RSI(70), BB(102%), Stoch(100)
17:49:32 | scanner    | INFO  | 🎯 2 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:49:32 | bot        | INFO  | 📊 Bakiye: $5141.79 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:49:32 | bot        | INFO  | ⏳ 60s bekleniyor...
17:50:32 | bot        | INFO  |
🔄 Döngü #47 başlıyor...
17:50:49 | strategy   | INFO  | 🎯 SİNYAL: ESP/USDT:USDT SHORT | Skor: 120 | ADX(26)+DI-, SMA50_OE(8.3%), RSI(66), BB(100%), Stoch(100)
17:50:59 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(3.4%), RSI(72), BB(102%), Stoch(100), MFI(86)
17:51:00 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.3%), RSI(70), BB(103%), Stoch(100)
17:51:10 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: ESP/USDT:USDT skor:120)
17:51:11 | bot        | INFO  | 📊 Bakiye: $5124.12 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:51:11 | bot        | INFO  | ⏳ 60s bekleniyor...
17:52:11 | bot        | INFO  |
🔄 Döngü #48 başlıyor...
17:52:27 | strategy   | INFO  | 🎯 SİNYAL: ESP/USDT:USDT SHORT | Skor: 120 | ADX(26)+DI-, SMA50_OE(8.5%), RSI(67), BB(101%), Stoch(100)
17:52:38 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(3.4%), RSI(72), BB(102%), Stoch(100), MFI(86)
17:52:39 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.3%), RSI(70), BB(103%), Stoch(100)
17:52:46 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(5.4%), RSI(71), BB(96%)
17:52:49 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: ESP/USDT:USDT skor:120)
17:52:49 | bot        | INFO  | 📊 Bakiye: $5125.78 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:52:49 | bot        | INFO  | ⏳ 60s bekleniyor...
17:53:49 | bot        | INFO  |
🔄 Döngü #49 başlıyor...
17:54:04 | strategy   | INFO  | 🎯 SİNYAL: ESP/USDT:USDT SHORT | Skor: 100 | ADX(26)+DI-, SMA50_OE(7.0%), RSI(65), BB(96%), Stoch(100)
17:54:14 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(3.3%), RSI(71), BB(101%), Stoch(100), MFI(86)
17:54:15 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(6.6%), RSI(71), BB(106%), Stoch(100), MFI(81)
17:54:22 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(5.4%), RSI(71), BB(97%)
17:54:26 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:54:26 | bot        | INFO  | 📊 Bakiye: $5116.10 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:54:26 | bot        | INFO  | ⏳ 60s bekleniyor...
17:55:26 | bot        | INFO  |
🔄 Döngü #50 başlıyor...
17:55:51 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(3.0%), RSI(69), BB(97%), Stoch(97), MFI(86)
17:55:52 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(6.7%), RSI(71), BB(106%), Stoch(100), MFI(81)
17:55:59 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(5.5%), RSI(72), BB(97%)
17:56:02 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:56:02 | bot        | INFO  | 📊 Bakiye: $5107.46 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:56:02 | bot        | INFO  | ⏳ 60s bekleniyor...
17:57:02 | bot        | INFO  |
🔄 Döngü #51 başlıyor...
17:57:29 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(3.1%), RSI(70), BB(98%), Stoch(98), MFI(86)
17:57:30 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(6.9%), RSI(71), BB(107%), Stoch(100), MFI(81)
17:57:34 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.0%), RSI(70), BB(99%), Stoch(96)
17:57:39 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(5.5%), RSI(72), BB(97%)
17:57:42 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:57:42 | bot        | INFO  | 📊 Bakiye: $5136.03 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:57:42 | bot        | INFO  | ⏳ 60s bekleniyor...
17:58:42 | bot        | INFO  |
🔄 Döngü #52 başlıyor...
17:58:48 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 110 | ADX(47)+DI-, SMA50_OE(4.1%), RSI(66), BB(94%), Stoch(89)
17:59:10 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 120 | ADX(32)+DI-, SMA50_OE(2.9%), RSI(68), BB(96%), Stoch(96), MFI(86)
17:59:11 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(6.7%), RSI(71), BB(107%), Stoch(100), MFI(81)
17:59:13 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.4%), RSI(72), BB(102%), Stoch(99)
17:59:19 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 100 | ADX(27)+DI-, SMA50_OE(5.6%), RSI(72), BB(99%)
17:59:22 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: STABLE/USDT:USDT skor:120)
17:59:22 | bot        | INFO  | 📊 Bakiye: $5130.49 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
17:59:22 | bot        | INFO  | ⏳ 60s bekleniyor...
18:00:22 | bot        | INFO  |
🔄 Döngü #53 başlıyor...
18:00:27 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 120 | ADX(47)+DI-, SMA50_OE(4.3%), RSI(67), BB(97%), Stoch(90)
18:00:48 | strategy   | INFO  | 🎯 SİNYAL: STABLE/USDT:USDT SHORT | Skor: 110 | ADX(32)+DI-, SMA50_OE(2.8%), RSI(67), BB(94%), Stoch(94), MFI(86)
18:00:49 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(6.8%), RSI(71), BB(107%), Stoch(100), MFI(81)
18:00:52 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.7%), RSI(74), MACD-, BB(85%), Stoch(86)
18:00:58 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 100 | ADX(28)+DI-, SMA50_OE(5.7%), RSI(72), BB(99%)
18:01:01 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: CUDIS/USDT:USDT skor:120)
18:01:01 | bot        | INFO  | 📊 Bakiye: $5141.98 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
18:01:01 | bot        | INFO  | ⏳ 60s bekleniyor...
18:02:01 | bot        | INFO  |
🔄 Döngü #54 başlıyor...
18:02:06 | strategy   | INFO  | 🎯 SİNYAL: CUDIS/USDT:USDT SHORT | Skor: 110 | ADX(49)+DI-, SMA50_OE(4.2%), RSI(67), BB(91%), Stoch(85)
18:02:28 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(7.2%), RSI(73), BB(103%), Stoch(100), MFI(94)
18:02:31 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.6%), RSI(73), MACD-, BB(84%), Stoch(83)
18:02:35 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(5.9%), RSI(73), BB(97%), Stoch(89)
18:02:38 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: ARC/USDT:USDT skor:120)
18:02:39 | bot        | INFO  | 📊 Bakiye: $5184.19 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
18:02:39 | bot        | INFO  | ⏳ 60s bekleniyor...
18:03:39 | bot        | INFO  |
🔄 Döngü #55 başlıyor...
18:04:05 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(7.6%), RSI(73), BB(105%), Stoch(100), MFI(94)
18:04:13 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(6.0%), RSI(74), BB(98%), Stoch(90)
18:04:15 | scanner    | INFO  | 🎯 2 sinyal bulundu (top: ARC/USDT:USDT skor:120)
18:04:16 | bot        | INFO  | 📊 Bakiye: $5158.15 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
18:04:16 | bot        | INFO  | ⏳ 60s bekleniyor...
18:05:16 | bot        | INFO  |
🔄 Döngü #56 başlıyor...
18:05:43 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(8.0%), RSI(74), BB(107%), Stoch(100), MFI(94)
18:05:50 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(6.3%), RSI(74), BB(100%), Stoch(90)
18:05:53 | scanner    | INFO  | 🎯 2 sinyal bulundu (top: ARC/USDT:USDT skor:120)
18:05:53 | bot        | INFO  | 📊 Bakiye: $5134.75 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
18:05:53 | bot        | INFO  | ⏳ 60s bekleniyor...
18:06:53 | bot        | INFO  |
🔄 Döngü #57 başlıyor...
18:07:22 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(7.9%), RSI(74), BB(107%), Stoch(100), MFI(94)
18:07:29 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | ADX(28)+DI-, SMA50_OE(6.3%), RSI(74), BB(100%), Stoch(90)
18:07:32 | scanner    | INFO  | 🎯 2 sinyal bulundu (top: ARC/USDT:USDT skor:120)
18:07:33 | bot        | INFO  | 📊 Bakiye: $5147.07 | Açık: 5 | Günlük PnL: $-18.48 | W/L: 0/2
18:07:33 | bot        | INFO  | ⏳ 60s bekleniyor...
18:08:33 | bot        | INFO  |
🔄 Döngü #58 başlıyor...
18:08:34 | exchange   | INFO  | 🗑️ Tüm emirler iptal edildi: Q/USDT:USDT
18:08:35 | exchange   | ERROR | ❌ Pozisyon kapatılamadı Q/USDT:USDT: binance {"code":-2022,"msg":"ReduceOnly Order is rejected."}
18:08:35 | portfolio  | INFO  | 🗑️ Pozisyon silindi: Q/USDT:USDT | STOP LOSS | PnL: $-6.55
18:08:35 | httpx      | INFO  | HTTP Request: POST <https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage> "HTTP/1.1 200 OK"
18:08:35 | trader     | INFO  | ❌ Q/USDT:USDT kapatıldı: STOP LOSS | PnL: -2.69% ($-6.55)
18:09:00 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(7.9%), RSI(74), BB(107%), Stoch(100), MFI(94)
18:09:03 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.6%), RSI(73), MACD-, BB(84%), Stoch(84)
18:09:07 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | ADX(29)+DI-, SMA50_OE(7.1%), RSI(76), BB(107%), Stoch(90)
18:09:10 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: ARC/USDT:USDT skor:120)
18:09:11 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
18:09:12 | exchange   | INFO  | ⚙️ ARC/USDT:USDT kaldıraç: 5x
18:09:12 | exchange   | INFO  | 📉 SHORT açıldı: ARC/USDT:USDT | Miktar: 18832.0738
18:09:12 | portfolio  | INFO  | 📋 Pozisyon kayıtlı: <Position ARC/USDT:USDT SHORT @ 0.07832 | Remaining: 100%>
18:09:12 | exchange   | INFO  | 🛑 SL ayarlandı: ARC/USDT:USDT @ 0.080975
18:09:13 | exchange   | INFO  | 🎯 TP ayarlandı: ARC/USDT:USDT @ 0.073597
18:09:13 | httpx      | INFO  | HTTP Request: POST https://api.telegram.org/bot7598737610:AAHSHVPCB98YjyV4s_4eEU-bmrhGx2akW1k/sendMessage "HTTP/1.1 200 OK"
18:09:13 | trader     | INFO  | ✅ ARC/USDT:USDT SHORT açıldı @ 0.07832 | Margin: $295.06
18:09:15 | bot        | INFO  | 📊 Bakiye: $5182.77 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:09:15 | bot        | INFO  | ⏳ 60s bekleniyor...
18:10:15 | bot        | INFO  |
🔄 Döngü #59 başlıyor...
18:10:42 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(7.9%), RSI(74), BB(107%), Stoch(100), MFI(94)
18:10:44 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.7%), RSI(74), MACD-, BB(86%), Stoch(86)
18:10:49 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 120 | ADX(29)+DI-, SMA50_OE(7.0%), RSI(76), BB(106%), Stoch(90)
18:10:52 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: ARC/USDT:USDT skor:120)
18:10:52 | bot        | INFO  | 📊 Bakiye: $5183.17 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:10:52 | bot        | INFO  | ⏳ 60s bekleniyor...
18:11:52 | bot        | INFO  |
🔄 Döngü #60 başlıyor...
18:12:20 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(8.1%), RSI(74), BB(108%), Stoch(100), MFI(94)
18:12:22 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.7%), RSI(74), MACD-, BB(86%), Stoch(86)
18:12:27 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 135 | ADX(29)+DI-, SMA50_OE(6.0%), RSI(74), BB(98%), Stoch(90), MFI(80)
18:12:30 | scanner    | INFO  | 🎯 3 sinyal bulundu (top: Q/USDT:USDT skor:135)
18:12:30 | bot        | INFO  | 📊 Bakiye: $5181.57 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:12:30 | bot        | INFO  | ⏳ 60s bekleniyor...
18:13:30 | bot        | INFO  |
🔄 Döngü #61 başlıyor...
18:13:51 | strategy   | INFO  | 🎯 SİNYAL: 我踏马来了/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(7.5%), RSI(66), BB(121%), Stoch(89)
18:13:55 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(28)+DI-, SMA50_OE(5.3%), RSI(65), BB(98%)
18:13:57 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(8.3%), RSI(75), BB(109%), Stoch(100), MFI(94)
18:14:00 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.8%), RSI(74), MACD-, BB(86%), Stoch(87)
18:14:05 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 135 | ADX(29)+DI-, SMA50_OE(6.5%), RSI(75), BB(102%), Stoch(90), MFI(80)
18:14:08 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: Q/USDT:USDT skor:135)
18:14:08 | bot        | INFO  | 📊 Bakiye: $5189.16 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:14:08 | bot        | INFO  | ⏳ 60s bekleniyor...
18:15:08 | bot        | INFO  |
🔄 Döngü #62 başlıyor...
18:15:31 | strategy   | INFO  | 🎯 SİNYAL: 我踏马来了/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(7.3%), RSI(66), BB(108%), Stoch(97)
18:15:38 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 120 | DI->DI+, SMA50_OE(8.7%), RSI(75), BB(111%), Stoch(100), MFI(94)
18:15:40 | strategy   | INFO  | 🎯 SİNYAL: BAS/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(6.9%), RSI(73), BB(95%), Stoch(91)
18:15:40 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.9%), RSI(74), MACD-, BB(88%), Stoch(88)
18:15:45 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | ADX(31)+DI-, SMA50_OE(5.9%), RSI(74), BB(93%), Stoch(98)
18:15:48 | scanner    | INFO  | 🎯 5 sinyal bulundu (top: ARC/USDT:USDT skor:120)
18:15:48 | bot        | INFO  | 📊 Bakiye: $5171.25 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:15:48 | bot        | INFO  | ⏳ 60s bekleniyor...
18:16:48 | bot        | INFO  |
🔄 Döngü #63 başlıyor...
18:17:10 | strategy   | INFO  | 🎯 SİNYAL: 我踏马来了/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(7.3%), RSI(66), BB(108%), Stoch(97)
18:17:17 | strategy   | INFO  | 🎯 SİNYAL: ARC/USDT:USDT SHORT | Skor: 135 | ADX(26)+DI-, SMA50_OE(7.2%), RSI(69), BB(96%), Stoch(93), MFI(84)
18:17:20 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.8%), RSI(75), MACD-, BB(86%), Stoch(97)
18:17:25 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | ADX(31)+DI-, SMA50_OE(5.7%), RSI(72), BB(91%), Stoch(95)
18:17:28 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: ARC/USDT:USDT skor:135)
18:17:28 | bot        | INFO  | 📊 Bakiye: $5168.27 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:17:28 | bot        | INFO  | ⏳ 60s bekleniyor...
18:18:28 | bot        | INFO  |
🔄 Döngü #64 başlıyor...
18:18:50 | strategy   | INFO  | 🎯 SİNYAL: 我踏马来了/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(7.9%), RSI(68), BB(114%), Stoch(97)
18:18:54 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(29)+DI-, SMA50_OE(6.0%), RSI(67), BB(100%)
18:19:01 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.6%), RSI(74), MACD-, BB(84%), Stoch(95)
18:19:06 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | ADX(31)+DI-, SMA50_OE(6.0%), RSI(74), BB(94%), Stoch(98)
18:19:09 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: Q/USDT:USDT skor:110)
18:19:10 | bot        | INFO  | 📊 Bakiye: $5169.26 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:19:10 | bot        | INFO  | ⏳ 60s bekleniyor...
18:20:10 | bot        | INFO  |
🔄 Döngü #65 başlıyor...
18:20:31 | strategy   | INFO  | 🎯 SİNYAL: 我踏马来了/USDT:USDT SHORT | Skor: 105 | DI->DI+, SMA50_OE(9.2%), RSI(70), BB(122%), Stoch(97)
18:20:36 | strategy   | INFO  | 🎯 SİNYAL: H/USDT:USDT SHORT | Skor: 100 | ADX(30)+DI-, SMA50_OE(6.4%), RSI(68), BB(104%)
18:20:41 | strategy   | INFO  | 🎯 SİNYAL: CYS/USDT:USDT SHORT | Skor: 100 | SMA50_OE(8.3%), RSI(71), MACD-, BB(81%), Stoch(83)
18:20:46 | strategy   | INFO  | 🎯 SİNYAL: Q/USDT:USDT SHORT | Skor: 110 | ADX(31)+DI-, SMA50_OE(6.0%), RSI(74), BB(94%), Stoch(98)
18:20:49 | scanner    | INFO  | 🎯 4 sinyal bulundu (top: Q/USDT:USDT skor:110)
18:20:49 | bot        | INFO  | 📊 Bakiye: $5179.03 | Açık: 5 | Günlük PnL: $-25.03 | W/L: 0/3
18:20:49 | bot        | INFO  | ⏳ 60s bekleniyor...
