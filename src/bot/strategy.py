import pandas as pd
import pandas_ta as ta
import logging
from .config import (
    MOMENTUM_THRESHOLD_PCT, VOLUME_THRESHOLD_MUL, SL_ATR_MULT, 
    TP1_RR, TP2_RR, TP3_RR,
    MTF_ENABLED, MTF_EMA_FAST, MTF_EMA_SLOW,
    PULLBACK_ENABLED, FIB_LEVELS, FIB_TIER_ALLOCATIONS, 
    PULLBACK_TIMEOUT_CANDLES, PULLBACK_IMMEDIATE_ALLOC
)

logger = logging.getLogger("strategy")


class PendingSignal:
    """
    🎯 Kademeli Fibonacci Pullback Sinyali
    - Momentum mumu tespit edilir
    - Fiyat Fibonacci seviyelerine ulaştıkça kademeli pozisyon açılır
    - Daha iyi giriş fiyatı, daha düşük risk
    """
    def __init__(self, symbol: str, side: str, momentum_high: float, momentum_low: float,
                 momentum_close: float, atr: float, reason: str, 
                 fib_levels: list = None, allocations: dict = None):
        self.symbol = symbol
        self.side = side
        self.momentum_high = momentum_high
        self.momentum_low = momentum_low
        self.momentum_close = momentum_close
        self.atr = atr
        self.reason = reason
        self.candles_waited = 0
        self.triggered_levels = []  # Tetiklenmiş seviyeler
        self.fully_triggered = False  # Tüm pozisyon açıldı mı?
        self.cancelled = False
        
        # Fibonacci seviyeleri ve pozisyon dağılımı
        self.fib_levels = fib_levels or FIB_LEVELS  # [0.382, 0.50, 0.618]
        self.allocations = allocations or FIB_TIER_ALLOCATIONS  # {0.382: 0.25, 0.50: 0.25, 0.618: 0.50}
        
        # Her seviye için hedef fiyatları hesapla
        candle_range = momentum_high - momentum_low
        self.level_targets = {}
        self.level_invalidations = {}
        
        if side == 'LONG':
            # LONG: Yükseliş sonrası geri çekilme seviyeleri
            for level in self.fib_levels:
                retracement = candle_range * level
                self.level_targets[level] = momentum_close - retracement
                # İnvalidation: Bir sonraki seviyenin %20 altı
                next_level = self._get_next_level(level)
                if next_level:
                    invalidation_retreat = candle_range * next_level * 1.2
                    self.level_invalidations[level] = momentum_close - invalidation_retreat
                else:
                    self.level_invalidations[level] = momentum_close - (candle_range * 0.8)
        else:
            # SHORT: Düşüş sonrası geri çekilme seviyeleri
            for level in self.fib_levels:
                retracement = candle_range * level
                self.level_targets[level] = momentum_close + retracement
                next_level = self._get_next_level(level)
                if next_level:
                    invalidation_retreat = candle_range * next_level * 1.2
                    self.level_invalidations[level] = momentum_close + invalidation_retreat
                else:
                    self.level_invalidations[level] = momentum_close + (candle_range * 0.8)
    
    def _get_next_level(self, current_level: float) -> float | None:
        """Bir sonraki Fibonacci seviyesini bul"""
        sorted_levels = sorted(self.fib_levels)
        idx = sorted_levels.index(current_level)
        if idx + 1 < len(sorted_levels):
            return sorted_levels[idx + 1]
        return None
    
    def check_pullback(self, current_price: float) -> dict:
        """
        🎯 Pullback durumunu kontrol et ve tetiklenen seviyeleri döndür
        Returns: {
            'status': 'WAITING' | 'LEVEL_HIT' | 'CANCELLED' | 'COMPLETE',
            'levels': [{'level': 0.382, 'allocation': 0.25, 'price': 123.45}, ...],
            'total_allocated': 0.50
        }
        """
        if self.cancelled or self.fully_triggered:
            return {'status': 'COMPLETE', 'levels': [], 'total_allocated': 1.0}
        
        self.candles_waited += 1
        
        # Zaman aşımı kontrolü
        if self.candles_waited > PULLBACK_TIMEOUT_CANDLES:
            self.cancelled = True
            return {'status': 'CANCELLED', 'levels': [], 'total_allocated': sum(self.allocations.get(l, 0) for l in self.triggered_levels)}
        
        triggered = []
        remaining_levels = [l for l in self.fib_levels if l not in self.triggered_levels]
        
        for level in remaining_levels:
            target = self.level_targets[level]
            invalidation = self.level_invalidations[level]
            
            if self.side == 'LONG':
                # Fiyat hedefe ulaştı mı?
                if current_price <= target:
                    self.triggered_levels.append(level)
                    triggered.append({
                        'level': level,
                        'allocation': self.allocations.get(level, 0.33),
                        'price': current_price
                    })
                # Çok düştü mü? (Trend kırıldı)
                elif current_price <= invalidation:
                    self.cancelled = True
                    return {'status': 'CANCELLED', 'levels': [], 'total_allocated': 0}
            else:  # SHORT
                if current_price >= target:
                    self.triggered_levels.append(level)
                    triggered.append({
                        'level': level,
                        'allocation': self.allocations.get(level, 0.33),
                        'price': current_price
                    })
                elif current_price >= invalidation:
                    self.cancelled = True
                    return {'status': 'CANCELLED', 'levels': [], 'total_allocated': 0}
        
        # Tüm seviyeler tetiklendi mi?
        if len(self.triggered_levels) >= len(self.fib_levels):
            self.fully_triggered = True
        
        if triggered:
            total_allocated = sum(self.allocations.get(l, 0) for l in self.triggered_levels)
            return {
                'status': 'LEVEL_HIT',
                'levels': triggered,
                'total_allocated': total_allocated
            }
        
        return {'status': 'WAITING', 'levels': [], 'total_allocated': sum(self.allocations.get(l, 0) for l in self.triggered_levels)}


class Strategy:
    """
    ⚡ MOMENTUM SCALPING STRATEGY v2.0
    - Multi-Timeframe Trend Confirmation
    - Pullback Entry (Geri çekilmede giriş)
    """

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gerekli indikatörleri hesaplar. 
        Momentum için ATR ve MA gibi yardımcı veriler eklenebilir.
        """
        if df is None or df.empty:
            return df

        # ATR (SL hesabı için gerekli)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        # Hacim Ortalaması (Patlama tespiti için)
        df['vol_ma'] = ta.sma(df['volume'], length=20)
        
        return df
    
    def calculate_mtf_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        🔄 Multi-Timeframe indikatörleri (15m/1h)
        EMA crossover ile trend yönünü belirler
        """
        if df is None or df.empty:
            return df
        
        df['ema_fast'] = ta.ema(df['close'], length=MTF_EMA_FAST)
        df['ema_slow'] = ta.ema(df['close'], length=MTF_EMA_SLOW)
        
        return df
    
    def get_mtf_trend(self, df_mtf: pd.DataFrame) -> str:
        """
        🔄 Üst zaman dilimi trend yönünü belirle
        Returns: 'BULLISH' | 'BEARISH' | 'NEUTRAL'
        """
        if df_mtf is None or len(df_mtf) < MTF_EMA_SLOW + 1:
            return 'NEUTRAL'
        
        df_mtf = self.calculate_mtf_indicators(df_mtf)
        
        last = df_mtf.iloc[-2]  # Tamamlanmış mumu kullan
        ema_fast = last['ema_fast']
        ema_slow = last['ema_slow']
        
        if pd.isna(ema_fast) or pd.isna(ema_slow):
            return 'NEUTRAL'
        
        # EMA farkı yüzdesel olarak değerlendirme
        diff_pct = ((ema_fast - ema_slow) / ema_slow) * 100
        
        if diff_pct > 0.1:  # EMA9 > EMA21 (%0.1'den fazla)
            return 'BULLISH'
        elif diff_pct < -0.1:  # EMA9 < EMA21
            return 'BEARISH'
        else:
            return 'NEUTRAL'

    def generate_signal(self, symbol: str, df: pd.DataFrame, df_mtf: pd.DataFrame = None) -> dict:
        """
        Mum verilerini analiz eder ve sinyal üretir.
        
        Sinyal formatı:
        {
            'symbol': 'BTCUSDT',
            'side': 'LONG' | 'SHORT' | 'WAIT' | 'PENDING_PULLBACK',
            'entry_price': 123.45,
            'sl': 120.0,
            'tp1': 125.0,
            ...
        }
        """
        if df is None or len(df) < 21:  # +1 for using completed candle
            return {'side': 'WAIT'}

        # CRITICAL FIX: Use last COMPLETED candle (-2), not incomplete current candle (-1)
        # The last candle (-1) is still forming and its close price can change
        last_candle = df.iloc[-2]
        
        # 🟢 LONG/SHORT ŞARTLARI
        # 1. Mum gövdesi % threshold'dan büyük mü?
        body_pct = (last_candle['close'] - last_candle['open']) / last_candle['open'] * 100
        
        # 2. Hacim ortalamanın üzerinde mi? (Son 20 mumun ortalaması)
        vol_ma = df['vol_ma'].iloc[-1]
        vol_spike = last_candle['volume'] > (vol_ma * VOLUME_THRESHOLD_MUL)
        
        side = 'WAIT'
        reason = ""

        if body_pct >= MOMENTUM_THRESHOLD_PCT and vol_spike:
            side = 'LONG'
            reason = f"🚀 Momentum: %{body_pct:.2f} yükseliş + Hacim Patlaması"
        
        elif body_pct <= -MOMENTUM_THRESHOLD_PCT and vol_spike:
            side = 'SHORT'
            reason = f"🔻 Momentum: %{body_pct:.2f} düşüş + Hacim Patlaması"

        if side == 'WAIT':
            return {'side': 'WAIT'}
        
        # 🔄 MULTI-TIMEFRAME CONFIRMATION
        if MTF_ENABLED and df_mtf is not None:
            mtf_trend = self.get_mtf_trend(df_mtf)
            
            # Trend uyuşmazlık kontrolü
            if side == 'LONG' and mtf_trend == 'BEARISH':
                logger.info(f"⚠️ {symbol} LONG sinyali atlandı: 15m trend BEARISH")
                return {'side': 'WAIT', 'reason': 'MTF_CONFLICT'}
            
            if side == 'SHORT' and mtf_trend == 'BULLISH':
                logger.info(f"⚠️ {symbol} SHORT sinyali atlandı: 15m trend BULLISH")
                return {'side': 'WAIT', 'reason': 'MTF_CONFLICT'}
            
            # Trend teyidi varsa reason'a ekle
            if mtf_trend != 'NEUTRAL':
                reason += f" | 🔄 15m Trend: {mtf_trend}"

        # ATR hesaplama
        atr = last_candle['atr']
        if pd.isna(atr) or atr <= 0:
            recent_range = (df['high'] - df['low']).tail(14).mean()
            if pd.isna(recent_range) or recent_range <= 0:
                logger.warning(f"⚠️ {symbol}: ATR hesaplanamadı, sinyal atlanıyor")
                return {'side': 'WAIT'}
            atr = recent_range
        
        # 🎯 PULLBACK ENTRY (Kademeli Fibonacci)
        if PULLBACK_ENABLED:
            # YENİ STRATEJI: %X hemen gir, kalanı pullback bekle
            immediate_alloc = PULLBACK_IMMEDIATE_ALLOC  # ENV'den okunur (varsayılan 0.50)
            
            # Pullback kuyruğu oluştur (kalan kısım için)
            pending = PendingSignal(
                symbol=symbol,
                side=side,
                momentum_high=last_candle['high'],
                momentum_low=last_candle['low'],
                momentum_close=last_candle['close'],
                atr=atr,
                reason=reason,
                # Kalan %50'nin dağılımı
                fib_levels=FIB_LEVELS,
                allocations={
                    lvl: alloc / (1 - immediate_alloc)  # Normalize et
                    for lvl, alloc in FIB_TIER_ALLOCATIONS.items()
                    if isinstance(lvl, float)  # Sadece sayısal seviyeler
                }
            )
            
            # Detaylı log
            level_info = []
            for lvl, target in pending.level_targets.items():
                alloc = pending.allocations.get(lvl, 0) * (1 - immediate_alloc)
                level_info.append(f"Fib{lvl*100:.1f}%@{target:.4f}({alloc:.0%})")
            
            logger.info(f"🎯 {symbol} HİBRİT GİRİŞ: {side}")
            logger.info(f"   ⚡ Hemen: {immediate_alloc:.0%} | ⏳ Pullback: {1-immediate_alloc:.0%}")
            logger.info(f"   📊 Seviyeler: {' | '.join(level_info)}")
            logger.info(f"   ⏰ Timeout: {PULLBACK_TIMEOUT_CANDLES} mum")
            
            # Hemen giriş sinyali + Pullback kuyruğu
            immediate_signal = self._build_tiered_signal(
                symbol=symbol,
                side_type=side,
                entry_price=last_candle['close'],
                atr=atr,
                reason=reason + " | ⚡ Hemen Giriş",
                allocation=immediate_alloc
            )
            immediate_signal['pending_pullback'] = pending  # Kalanı için
            
            return immediate_signal
        
        # Pullback devre dışıysa direkt giriş
        current_candle = df.iloc[-1]
        price = current_candle['close']
        
        return self._build_signal(symbol, side, price, atr, reason)
    
    def process_pullback(self, pending: PendingSignal, current_price: float) -> dict:
        """
        🎯 Bekleyen pullback sinyalini kontrol et ve kademeli sinyaller üret
        Her Fibonacci seviyesine ulaşıldığında pozisyonun bir kısmı açılır
        """
        result = pending.check_pullback(current_price)
        status = result['status']
        
        if status == 'CANCELLED':
            logger.info(f"❌ {pending.symbol} PULLBACK IPTAL: {pending.candles_waited} mum bekledi")
            return {
                'side': 'CANCELLED', 
                'symbol': pending.symbol,
                'total_allocated': result.get('total_allocated', 0)
            }
        
        if status == 'LEVEL_HIT':
            # Yeni seviye(ler) tetiklendi
            for level_info in result['levels']:
                lvl = level_info['level']
                alloc = level_info['allocation']
                logger.info(f"✅ {pending.symbol} FİBO {lvl*100:.1f}% TETİKLENDİ @ {current_price:.4f} | Pozisyon: {alloc:.0%}")
            
            # Kademeli sinyal döndür
            return {
                'side': 'TIERED_ENTRY',
                'symbol': pending.symbol,
                'side_type': pending.side,
                'entry_price': current_price,
                'atr': pending.atr,
                'reason': pending.reason + f" | 📈 Fibo {lvl*100:.1f}% ({alloc:.0%})",
                'levels': result['levels'],
                'total_allocated': result['total_allocated'],
                'pending_signal': pending
            }
        
        # Hala bekliyor
        allocated = result.get('total_allocated', 0)
        return {
            'side': 'WAITING',
            'symbol': pending.symbol,
            'pending_signal': pending,
            'total_allocated': allocated
        }
    
    def _build_tiered_signal(self, symbol: str, side_type: str, entry_price: float, 
                              atr: float, reason: str, allocation: float) -> dict:
        """
        📦 Kademeli pozisyon için sinyal objesi oluştur
        allocation: Bu seviye için açılacak pozisyon yüzdesi (0.25, 0.25, 0.50)
        """
        risk = atr * SL_ATR_MULT
        
        if side_type == 'LONG':
            sl = entry_price - risk
            tp1 = entry_price + (risk * TP1_RR)
            tp2 = entry_price + (risk * TP2_RR)
            tp3 = entry_price + (risk * TP3_RR)
        else:
            sl = entry_price + risk
            tp1 = entry_price - (risk * TP1_RR)
            tp2 = entry_price - (risk * TP2_RR)
            tp3 = entry_price - (risk * TP3_RR)

        return {
            'symbol': symbol,
            'side': side_type,
            'entry_price': entry_price,
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'reason': reason,
            'allocation': allocation  # Bu pozisyonun toplam içindeki yüzdesi
        }
    
    def _build_signal(self, symbol: str, side: str, price: float, atr: float, reason: str) -> dict:
        """
        📦 Sinyal objesi oluştur
        """
        risk = atr * SL_ATR_MULT
        
        if side == 'LONG':
            sl = price - risk
            tp1 = price + (risk * TP1_RR)
            tp2 = price + (risk * TP2_RR)
            tp3 = price + (risk * TP3_RR)
        else:
            sl = price + risk
            tp1 = price - (risk * TP1_RR)
            tp2 = price - (risk * TP2_RR)
            tp3 = price - (risk * TP3_RR)

        return {
            'symbol': symbol,
            'side': side,
            'entry_price': price,
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'reason': reason
        }
