"""
🔌 Binance Futures Exchange Connector (CCXT)
Paper trading + canlı trading desteği
"""
import ccxt
import logging
from .config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, EXCHANGE_SANDBOX, LEVERAGE
)

logger = logging.getLogger("exchange")


class ExchangeClient:
    """Binance Futures bağlantı katmanı"""

    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_API_SECRET,
            'options': {
                'defaultType': 'future',
                'warnOnFetchOpenOrdersWithoutSymbol': False,
            },
            'enableRateLimit': True,
        })

        if EXCHANGE_SANDBOX:
            # CCXT v4.5.6+ Demo Trading (Mock Trading) yapılandırması
            # Sandbox mode (True) eski testnet'e gittiği için bunu kullanmıyoruz.
            # Bunun yerine demo trading'i aktif edip URL'leri yönlendiriyoruz.
            if hasattr(self.exchange, 'enable_demo_trading'):
                self.exchange.enable_demo_trading(True)
            
            self.exchange.urls['api']['fapiPublic'] = 'https://demo-fapi.binance.com/fapi/v1'
            self.exchange.urls['api']['fapiPrivate'] = 'https://demo-fapi.binance.com/fapi/v1'
            
            logger.info("🧪 DEMO TRADING (Mock) modu aktif")
        else:
            logger.warning("⚠️ CANLI TRADING modu aktif!")

    def get_balance(self) -> dict:
        """Futures cüzdan bakiyesini döndür"""
        try:
            balance = self.exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            return {
                'total': float(usdt.get('total', 0)),
                'free': float(usdt.get('free', 0)),
                'used': float(usdt.get('used', 0)),
            }
        except Exception as e:
            # Başlangıçta bakiye alınamazsa çok gürültü yapmasın (retry mekanizması main'de var)
            logger.debug(f"Bakiye alınamadı: {e}")
            return {'total': 0, 'free': 0, 'used': 0}

    def get_positions(self) -> list:
        """Açık pozisyonları listele"""
        try:
            positions = self.exchange.fetch_positions()
            return [p for p in positions if float(p.get('contracts', 0)) > 0]
        except Exception as e:
            logger.error(f"❌ Pozisyonlar alınamadı: {e}")
            return []

    def set_leverage(self, symbol: str, leverage: int = LEVERAGE):
        """Kaldıracı ayarla"""
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.info(f"⚙️ {symbol} kaldıraç: {leverage}x")
        except Exception as e:
            logger.warning(f"⚠️ {symbol} kaldıraç ayarlanamadı: {e}")

    def set_margin_mode(self, symbol: str, mode: str = "isolated"):
        """Marjin modunu ayarla (isolated/cross)"""
        try:
            self.exchange.set_margin_mode(mode, symbol)
        except Exception as e:
            # Zaten ayarlıysa hata verir, sorun değil
            pass

    def open_short(self, symbol: str, amount: float) -> dict | None:
        """Short pozisyon aç"""
        try:
            self.set_leverage(symbol)
            self.set_margin_mode(symbol)
            order = self.exchange.create_market_sell_order(
                symbol, amount, params={'reduceOnly': False}
            )
            logger.info(f"📉 SHORT açıldı: {symbol} | Miktar: {amount}")
            return order
        except Exception as e:
            logger.error(f"❌ SHORT açılamadı {symbol}: {e}")
            return None

    def open_long(self, symbol: str, amount: float) -> dict | None:
        """Long pozisyon aç"""
        try:
            self.set_leverage(symbol)
            self.set_margin_mode(symbol)
            order = self.exchange.create_market_buy_order(
                symbol, amount, params={'reduceOnly': False}
            )
            logger.info(f"📈 LONG açıldı: {symbol} | Miktar: {amount}")
            return order
        except Exception as e:
            logger.error(f"❌ LONG açılamadı {symbol}: {e}")
            return None

    def close_position(self, symbol: str, side: str, amount: float) -> dict | None:
        """Pozisyonu kapat (kısmi veya tam)"""
        try:
            if side == 'SHORT':
                order = self.exchange.create_market_buy_order(
                    symbol, amount, params={'reduceOnly': True}
                )
            else:
                order = self.exchange.create_market_sell_order(
                    symbol, amount, params={'reduceOnly': True}
                )
            logger.info(f"✅ Pozisyon kapatıldı: {symbol} | {amount}")
            return order
        except Exception as e:
            if "ReduceOnly Order is rejected" in str(e):
                logger.info(f"ℹ️ {symbol} pozisyonu zaten borsa tarafında (SL/TP) kapanmış.")
            else:
                logger.error(f"❌ Pozisyon kapatılamadı {symbol}: {e}")
            return None

    def set_stop_loss(self, symbol: str, side: str, stop_price: float, amount: float = 0) -> dict | None:
        """Stop loss emri koy (Pozisyona bağlı — closePosition)"""
        try:
            # Önce varsa semboldeki tüm SL/TP emirlerini temizle (Çakışmayı önlemek için)
            # Binance tek bir yönde sadece bir closePosition=True emrine izin verir
            self.cancel_all_orders(symbol)
            import time
            time.sleep(1.0) # Borsa motoruna vakit tanı (Binance -4130 hatası için artırıldı)
            
            sl_side = 'buy' if side == 'SHORT' else 'sell'
            order = self.exchange.create_order(
                symbol, 'stop_market', sl_side, None,
                params={
                    'stopPrice': stop_price,
                    'closePosition': True,
                }
            )
            logger.info(f"🛑 SL ayarlandı: {symbol} @ {stop_price} (Pozisyona bağlı)")
            return order
        except Exception as e:
            if "code\":-4130" in str(e):
                logger.warning(f"⚠️ {symbol} SL zaten ayarlı veya çakışma var: {e}")
            else:
                logger.error(f"❌ SL ayarlanamadı {symbol}: {e}")
            return None

    def set_take_profit(self, symbol: str, side: str, tp_price: float, amount: float) -> dict | None:
        """Take profit emri koy"""
        try:
            tp_side = 'buy' if side == 'SHORT' else 'sell'
            order = self.exchange.create_order(
                symbol, 'take_profit_market', tp_side, amount,
                params={
                    'stopPrice': tp_price,
                    'reduceOnly': True,
                    'closePosition': False,
                }
            )
            logger.info(f"🎯 TP ayarlandı: {symbol} @ {tp_price}")
            return order
        except Exception as e:
            logger.error(f"❌ TP ayarlanamadı {symbol}: {e}")
            return None

    def cancel_all_orders(self, symbol: str):
        """Bir sembol için tüm açık emirleri iptal et"""
        try:
            self.exchange.cancel_all_orders(symbol)
            logger.info(f"🗑️ Tüm emirler iptal edildi: {symbol}")
        except Exception as e:
            logger.warning(f"⚠️ Emir iptali başarısız {symbol}: {e}")

    def get_open_orders(self, symbol: str = None) -> list:
        """Açık emirleri listele (sembol opsiyonel)"""
        try:
            if symbol:
                return self.exchange.fetch_open_orders(symbol)
            return self.exchange.fetch_open_orders()
        except Exception as e:
            logger.debug(f"Emir listesi alınamadı: {e}")
            return []

    def cleanup_orphan_orders(self, active_symbols: set):
        """
        🧹 YETİM EMİR TEMİZLİĞİ
        Aktif pozisyonu olmayan coinlerin bekleyen emirlerini iptal et.
        Sembol bazlı çalışır (rate limit dostu).
        """
        try:
            # Tüm açık emirleri çek
            open_orders = self.get_open_orders()
            if not open_orders:
                return
            
            # Emirlerdeki benzersiz sembolleri çıkar
            order_symbols = set()
            for order in open_orders:
                raw_sym = order.get('info', {}).get('symbol', '')
                if not raw_sym:
                    raw_sym = order['symbol'].replace('/', '').split(':')[0]
                order_symbols.add(raw_sym)
            
            # Aktif pozisyonu olmayan sembollerin emirlerini temizle
            orphan_symbols = order_symbols - active_symbols
            
            if orphan_symbols:
                logger.info(f"🧹 {len(orphan_symbols)} yetim sembol tespit edildi: {orphan_symbols}")
                for sym in orphan_symbols:
                    self.cancel_all_orders(sym)
                logger.info(f"✅ Yetim emirler temizlendi!")
                    
        except Exception as e:
            logger.warning(f"⚠️ Yetim emir temizliği atlandi: {e}")

    def fetch_ohlcv(self, symbol: str, timeframe: str = '15m', limit: int = 100) -> list:
        """OHLCV verisi çek"""
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        except Exception as e:
            if "Invalid symbol status" in str(e) or "code\":-1122" in str(e):
                logger.warning(f"⚠️ {symbol} şu an işlem görmüyor (Invalid Status)")
            else:
                logger.error(f"❌ OHLCV alınamadı {symbol}: {e}")
            return []

    def fetch_ticker(self, symbol: str) -> dict | None:
        """Anlık fiyat bilgisi (Retry ile)"""
        for i in range(3):
            try:
                return self.exchange.fetch_ticker(symbol)
            except Exception as e:
                if i < 2:
                    import time
                    time.sleep(1)
                    continue
                logger.error(f"❌ Ticker alınamadı {symbol}: {e}")
        return None

    def fetch_funding_rate(self, symbol: str) -> float:
        """Funding rate çek (Piyasa kalabalık göstergesi)"""
        try:
            funding = self.exchange.fetch_funding_rate(symbol)
            rate = float(funding.get('fundingRate', 0))
            return rate
        except Exception as e:
            logger.debug(f"Funding rate alınamadı {symbol}: {e}")
            return 0.0

    def get_market_limits(self, symbol: str) -> dict:
        """Market limitlerini getir (Min/Max miktar)"""
        try:
            # Market verisinin yüklü olduğundan emin ol
            if not self.exchange.markets:
                self.exchange.load_markets()
            
            market = self.exchange.market(symbol)
            info = market.get('info', {})
            filters = info.get('filters', [])
            
            # Varsayılan limitler
            min_qty = float(market['limits']['amount']['min'] or 0)
            max_qty = float(market['limits']['amount']['max'] or float('inf'))
            
            # Binance'e özel MARKET_LOT_SIZE kontrolü (Market emirleri için daha sıkı olabilir)
            for f in filters:
                if f.get('filterType') == 'MARKET_LOT_SIZE':
                    max_qty = float(f.get('maxQty', max_qty))
                    break
            
            return {
                'min_qty': min_qty,
                'max_qty': max_qty,
            }
        except Exception as e:
            logger.warning(f"⚠️ Market limitleri alınamadı {symbol}: {e}")
            return {'min_qty': 0.0, 'max_qty': float('inf')}

    def sanitize_amount(self, symbol: str, amount: float) -> float:
        """Miktarı market limitlerine (Min/Max/Precision) uygun hale getir"""
        try:
            limits = self.get_market_limits(symbol)
            
            original_amount = amount

            # Max limit kontrolü
            if amount > limits['max_qty']:
                logger.warning(f"⚠️ {symbol} miktar ({amount}) max limiti aşıyor. {limits['max_qty']} değerine çekildi.")
                amount = limits['max_qty']
            
            # Min limit kontrolü
            if amount < limits['min_qty']:
                logger.warning(f"⚠️ {symbol} miktar ({amount}) min limitin altında.")
                return 0.0

            # Step size / Precision
            final_amount = float(self.exchange.amount_to_precision(symbol, amount))
            
            if original_amount != final_amount:
                logger.info(f"📏 Miktar Ayarlandı {symbol}: {original_amount} -> {final_amount} (Max: {limits['max_qty']})")
            
            return final_amount
        except Exception as e:
            logger.error(f"❌ Miktar normalize edilemedi {symbol}: {e}")
            return amount

    def fetch_top_futures_symbols(self, count: int = 100) -> list[str]:
        """Hacme göre ilk N futures sembolünü getir"""
        try:
            markets = self.exchange.load_markets()
            futures = {
                s: m for s, m in markets.items()
                if m.get('swap') and m.get('quote') == 'USDT' and m.get('active')
            }

            tickers = self.exchange.fetch_tickers(list(futures.keys()))
            sorted_by_volume = sorted(
                tickers.values(),
                key=lambda t: float(t.get('quoteVolume', 0) or 0),
                reverse=True,
            )
            return [t['symbol'] for t in sorted_by_volume[:count]]
        except Exception as e:
            logger.error(f"❌ Top coinler alınamadı: {e}")
            return []

    def fetch_all_trade_history(self, limit_per_symbol: int = 500) -> list:
        """
        🚀 GÜVENLİ HİBRİT TARAMA: 
        'fetch_income' hatası riskine karşı bakiyeli ve pozisyonlu coinleri tarar.
        """
        try:
            target_symbols = set()
            
            # 1. Bakiye Kontrolü (En güvenli yöntem)
            try:
                # Tüm bakiyeleri çek (Sıfır olmayanları)
                balance = self.exchange.fetch_balance()
                for currency, data in balance.items():
                    if data['total'] > 0 and currency != 'USDT':
                        # Currency -> Symbol dönüşümü (örn: BTC -> BTC/USDT:USDT)
                        # Bu her zaman %100 tutmaz ama çoğu zaman işe yarar
                        try:
                            # Piyasada bu coin ile başlayan USDT çiftini bul
                            markets = self.exchange.load_markets()
                            for symbol in markets:
                                if symbol.startswith(f"{currency}/USDT"):
                                    target_symbols.add(symbol)
                                    break
                        except: pass
                logger.info(f"💰 Bakiyeli {len(target_symbols)} sembol bulundu.")
            except Exception as e:
                logger.warning(f"⚠️ Bakiye tarama hatası: {e}")

            # 2. Açık Pozisyonlar (Kesin işlem vardır)
            try:
                positions = self.exchange.fetch_positions()
                for p in positions:
                    if float(p.get('contracts', 0)) > 0 or float(p.get('info', {}).get('positionAmt', 0)) != 0:
                        target_symbols.add(p['symbol'])
                logger.info(f"🔍 Pozisyonlardan liste güncellendi. Toplam: {len(target_symbols)}")
            except Exception as e:
                logger.debug(f"Pozisyon tarama hatası: {e}")

            if not target_symbols:
                logger.warning("🚫 Taranacak aktif sembol bulunamadı. Fallback: Popüler işlem çiftleri taranıyor...")
                # Hiçbir şey bulamazsak popülerleri tara
                top_coins = [
                    'BTC/USDT:USDT', 'ETH/USDT:USDT', 'BNB/USDT:USDT', 'SOL/USDT:USDT', 'XRP/USDT:USDT',
                    'ADA/USDT:USDT', 'DOGE/USDT:USDT', 'AVAX/USDT:USDT', 'DOT/USDT:USDT', 'MATIC/USDT:USDT'
                ]
                target_symbols.update(top_coins)

            all_trades = []
            logger.info(f"🚀 {len(target_symbols)} sembol için detaylı geçmiş çekiliyor...")
            
            for symbol in target_symbols:
                try:
                    trades = self.fetch_trade_history(symbol, limit=limit_per_symbol)
                    if trades:
                        all_trades.extend(trades)
                except Exception as e:
                    logger.debug(f"{symbol} geçmişi çekilemedi: {e}")
                    continue
            
            # Zamana göre sırala (En yeni üstte)
            all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            logger.info(f"✅ Tarama tamamlandı. Toplam {len(all_trades)} işlem listelendi.")
            return all_trades

        except Exception as e:
            logger.error(f"❌ Güvenli tarama hatası: {e}")
            return []

    def fetch_trade_history(self, symbol: str = None, limit: int = 200) -> list:
        """Kullanıcının işlem geçmişini çek (CCXT fetchMyTrades)"""
        try:
            trades = self.exchange.fetch_my_trades(symbol, limit=limit)
            return trades if trades is not None else []
        except Exception as e:
            logger.error(f"❌ İşlem geçmişi alınamadı: {e}")
            return []
