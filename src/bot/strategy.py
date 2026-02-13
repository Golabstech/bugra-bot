"""
🧠 Strateji Sinyal Motoru
Backtest motorundan (backtest_csv_v2.py) aynen taşınan scoring mantığı.
Canlı OHLCV verisine uygulanarak sinyal üretir.
"""
import pandas as pd
import pandas_ta as ta
import logging
from .config import (
    STRATEGY_SIDE, SCORE_THRESHOLD, MIN_REASONS,
    MAX_ATR_PERCENT, MIN_ATR_PERCENT,
    SL_ATR_MULT, TP1_RR, TP2_RR, TP3_RR,
)

logger = logging.getLogger("strategy")


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Teknik indikatörleri hesapla"""
    df = df.copy()
    df['ema9'] = ta.ema(df['close'], length=9)
    df['ema21'] = ta.ema(df['close'], length=21)
    df['sma50'] = ta.sma(df['close'], length=50)
    df['rsi'] = ta.rsi(df['close'], length=14)

    macd = ta.macd(df['close'])
    if macd is not None:
        df['macd'] = macd.iloc[:, 0]
        df['macd_signal'] = macd.iloc[:, 2]
    else:
        df['macd'] = df['macd_signal'] = 0

    bb = ta.bbands(df['close'], length=20, std=2)
    if bb is not None:
        df['bb_lower'] = bb.iloc[:, 0]
        df['bb_middle'] = bb.iloc[:, 1]
        df['bb_upper'] = bb.iloc[:, 2]
        df['bb_pct'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    else:
        df['bb_pct'] = 0.5

    adx_data = ta.adx(df['high'], df['low'], df['close'], length=14)
    if adx_data is not None:
        df['adx'] = adx_data.iloc[:, 0]
        df['di_plus'] = adx_data.iloc[:, 1]
        df['di_minus'] = adx_data.iloc[:, 2]
    else:
        df['adx'] = df['di_plus'] = df['di_minus'] = 0

    stoch = ta.stochrsi(df['close'], length=14)
    if stoch is not None:
        df['stoch_k'] = stoch.iloc[:, 0]
    else:
        df['stoch_k'] = 50

    df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)
    df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

    # 📊 HACİM ANALİZİ
    # Hacim ortalaması (Mevcut mum hariç son 20 mum)
    df['vol_avg20'] = df['volume'].shift(1).rolling(window=20).mean()
    # Hacim oranı (Şu anki hacim / Önceki ortalama)
    df['vol_ratio'] = df['volume'] / df['vol_avg20']

    df = df.ffill().fillna(0).infer_objects(copy=False)
    return df


def score_short(row: pd.Series, prev_row: pd.Series = None) -> tuple[int, int, list[str]]:
    """Son mum için SHORT skor hesapla → (score, reason_count, reasons)"""
    score = 0
    reasons = []

    adx, di_plus, di_minus = row['adx'], row['di_plus'], row['di_minus']
    rsi, macd_val, macd_sig = row['rsi'], row['macd'], row['macd_signal']
    bb_pct, stoch_k, mfi = row['bb_pct'], row['stoch_k'], row['mfi']
    ema9, ema21, sma50 = row['ema9'], row['ema21'], row['sma50']

    # ADX + DI (Tek blok — çift sayım önlendi)
    # Düşük ADX = yatay piyasa = mean reversion'a uygun (SHORT için ideal)
    # Yüksek ADX = güçlü trend = mean reversion tehlikeli
    if adx < 25:
        score += 20
        reasons.append(f"ADX({adx:.0f})Low")
        if di_minus > di_plus:
            score += 5
            reasons.append("DI->DI+")
    elif adx <= 50:
        if di_minus > di_plus:
            score += 10
            reasons.append(f"ADX({adx:.0f})+DI-")
    else:
        score -= 10
        reasons.append("ADX-High")

    # SMA50 Overextension
    dist = (row['close'] - sma50) / sma50 * 100 if sma50 > 0 else 0
    if dist > 4:
        score += 25
        reasons.append(f"SMA50_OE({dist:.1f}%)")
    elif dist > 2:
        score += 10
        reasons.append(f"SMA50_OE({dist:.1f}%)")

    # RSI
    if rsi > 80:
        score += 30
        reasons.append(f"RSI({rsi:.0f})")
    elif rsi > 65:
        score += 20
        reasons.append(f"RSI({rsi:.0f})")
    elif rsi > 60:
        reasons.append(f"RSI({rsi:.0f})")

    # MACD
    if macd_val < macd_sig:
        score += 5
        reasons.append("MACD-")

    # Bollinger
    if bb_pct > 0.95:
        score += 25
        reasons.append(f"BB({bb_pct*100:.0f}%)")
    elif bb_pct > 0.8:
        score += 15
        reasons.append(f"BB({bb_pct*100:.0f}%)")

    # StochRSI
    if stoch_k > 80:
        score += 20
        reasons.append(f"Stoch({stoch_k:.0f})")

    # MFI
    if mfi > 80:
        score += 15
        reasons.append(f"MFI({mfi:.0f})")

    # EMA Bearish (nötr, sadece count)
    if ema9 < ema21 < sma50:
        reasons.append("EMA Bearish")

    return score, len(reasons), reasons


def score_long(row: pd.Series) -> tuple[int, int, list[str]]:
    """Son mum için LONG skor hesapla → (score, reason_count, reasons)"""
    score = 0
    reasons = []

    adx, di_plus, di_minus = row['adx'], row['di_plus'], row['di_minus']
    rsi, macd_val, macd_sig = row['rsi'], row['macd'], row['macd_signal']
    bb_pct, stoch_k = row['bb_pct'], row['stoch_k']
    ema9, ema21, sma50 = row['ema9'], row['ema21'], row['sma50']

    if row['close'] > sma50:
        score += 15
        reasons.append("BULL_REGIME")

    if rsi < 30:
        score += 40
        reasons.append(f"RSI({rsi:.0f})")
    elif rsi < 40:
        score += 20
        reasons.append(f"RSI({rsi:.0f})")

    if stoch_k < 20:
        score += 10
        reasons.append(f"Stoch_L({stoch_k:.0f})")

    if bb_pct < 0.1:
        score += 20
        reasons.append(f"BB_LOW({bb_pct*100:.0f}%)")
    elif bb_pct < 0.2:
        score += 10
        reasons.append(f"BB_LOW({bb_pct*100:.0f}%)")

    if ema9 > ema21:
        score += 15
        reasons.append("EMA Golden")

    if macd_val > macd_sig:
        score += 40
        reasons.append("MACD+")

    if adx > 25 and di_plus > di_minus:
        score += 20
        reasons.append(f"ADX({adx:.0f})+DI+")
    elif di_plus > di_minus:
        reasons.append("DI+>DI-")

    return score, len(reasons), reasons


def generate_signal(df: pd.DataFrame, symbol: str, include_all: bool = False, funding_rate: float = 0.0) -> dict | None:
    """
    OHLCV DataFrame'den sinyal üret.
    Sinyal varsa → {'symbol', 'side', 'score', 'reasons', 'entry_price', 'sl', 'tp1', 'tp2', 'tp3', 'atr'}
    Sinyal yoksa (ve include_all=False) → None
    """
    if len(df) < 50:
        return None

    df = calculate_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = float(last['close'])
    atr = float(last['atr'])

    # Volatilite filtresi
    atr_pct = (atr / price) * 100 if price > 0 else 0
    volatility_ok = MIN_ATR_PERCENT <= atr_pct <= MAX_ATR_PERCENT
    
    is_valid = True
    filter_reason = ""

    if not volatility_ok:
        is_valid = False
        filter_reason = "Volatility"
        if not include_all:
            return None

    side = STRATEGY_SIDE

    if side == 'SHORT':
        score, num_reasons, reasons = score_short(last, prev)
        
        # Boğa koruması ve Momentum Filtresi
        sma50 = float(last['sma50'])
        current_rsi = float(last['rsi'])
        prev_rsi = float(prev['rsi'])
        
        # 1. Momentum Filtresi (RSI 80+ ve hala artıyorsa girme)
        if current_rsi >= 80 and current_rsi >= prev_rsi:
            is_valid = False
            filter_reason = "Momentum"
            if not include_all: return None

        # 2. Hacim Patlaması Filtresi (Short Squeeze Koruması)
        # Önceki ortalamanın 3.5 katı hacim varsa risklidir.
        if float(last['vol_ratio']) > 3.5:
            is_valid = False
            filter_reason = "Volume"
            if not include_all: return None

        # 3. God Candle Filtresi (İğnesiz dev mum veya ATR patlaması)
        candle_body = abs(last['close'] - last['open'])
        # Eğer mum boyu, son 14 mumun ortalama hareketinin (ATR) 3 katından büyükse dikey patlamadır.
        if candle_body > (atr * 3):
            is_valid = False
            filter_reason = "GodCandle"
            if not include_all: return None

        candle_change = (last['close'] - last['open']) / last['open'] * 100
        wick_size = (last['high'] - last['close']) / (last['high'] - last['low']) if (last['high'] - last['low']) > 0 else 0
        if candle_change > 3.0 and wick_size < 0.15:
             is_valid = False
             filter_reason = "GodCandle"
             if not include_all: return None

        # 5. Kırmızı Mum Doğrulaması (Bearish Confirmation)
        # Son mum kırmızı olmalı (Close < Open) → Satıcılar geldi teyidi
        # Yeşil mumda short açmak = "dönüşü tahmin etmek", kırmızı mumda = "dönüşü teyit etmek"
        last_is_red = float(last['close']) < float(last['open'])
        prev_is_green = float(prev['close']) > float(prev['open'])
        
        if not last_is_red:
            # Son mum hala yeşil — satıcılar henüz gelmemiş
            is_valid = False
            filter_reason = "NoRedCandle"
            if not include_all: return None
        
        # BONUS: Eğer önceki yeşil mumdan sonra hacimli kırmızı mum geldiyse → ekstra güvence
        if last_is_red and prev_is_green:
            prev_vol = float(prev['volume']) if float(prev['volume']) > 0 else 1
            vol_confirmation = float(last['volume']) / prev_vol
            if vol_confirmation >= 0.7:
                score += 10  # Hacimli kırmızı mum = güçlü dönüş sinyali
                reasons.append("RedConfirm")
             
        # 4. Funding Rate Filtresi (Kalabalık Göstergesi)
        # Pozitif FR = Herkes long → Short kontrarian avantaj (+puan)
        # Negatif FR = Herkes short → Short kalabalık (-puan / block)
        fr_pct = funding_rate * 100  # 0.001 → 0.1%
        if fr_pct > 0.03:
            score += 15
            reasons.append(f"FR+({fr_pct:.2f}%)")
        elif fr_pct < -0.1:
            # Aşırı kalabalık: Short Squeeze riski çok yüksek
            is_valid = False
            filter_reason = "Funding"
            if not include_all: return None
        elif fr_pct < -0.05:
            score -= 15
            reasons.append(f"FR-({fr_pct:.2f}%)")

        # 5. Fiyat SMA50 üzerinde mi? (Boğa trendine kafa atma)
        if price > sma50:
            threshold = SCORE_THRESHOLD + 15
        else:
            threshold = SCORE_THRESHOLD
    else:
        score, num_reasons, reasons = score_long(last)
        threshold = SCORE_THRESHOLD

    if score < threshold or num_reasons < MIN_REASONS:
        is_valid = False
        filter_reason = "Score"
        if not include_all: return None

    # SL / TP hesapla
    risk = atr * SL_ATR_MULT
    if side == 'SHORT':
        sl = price + risk
        tp1 = price - (risk * TP1_RR)
        tp2 = price - (risk * TP2_RR)
        tp3 = price - (risk * TP3_RR)

        # R:R Kontrolü: BB Mid hedefi SL riskinin en az yarısını karşılamalı
        bb_mid_distance = price - float(last['bb_middle'])
        if bb_mid_distance < risk * 0.5 and is_valid:
            is_valid = False
            filter_reason = "BB_RR"
            if not include_all: return None
    else:
        sl = price - risk
        tp1 = price + (risk * TP1_RR)
        tp2 = price + (risk * TP2_RR)
        tp3 = price + (risk * TP3_RR)

    signal = {
        'symbol': symbol,
        'side': side,
        'score': score,
        'reasons': reasons,
        'num_reasons': num_reasons,
        'entry_price': price,
        'sl': round(sl, 6),
        'tp1': round(tp1, 6),
        'tp2': round(tp2, 6),
        'tp3': round(tp3, 6),
        'atr': atr,
        'atr_pct': atr_pct,
        'funding_rate': funding_rate,
        'bb_middle': float(last['bb_middle']),
        'bb_lower': float(last['bb_lower']),
        'bb_upper': float(last['bb_upper']),
        'is_valid': is_valid,
        'filter_reason': filter_reason
    }

    if is_valid:
        logger.info(f"🎯 SİNYAL: {symbol} {side} | Skor: {score} | {', '.join(reasons)}")
    
    return signal
