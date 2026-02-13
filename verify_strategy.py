
import pandas as pd
import numpy as np
from src.bot.strategy import Strategy

def test_strategy():
    strategy = Strategy()
    
    # Test verisi oluştur
    data = {
        'open': [100] * 50,
        'high': [105] * 50,
        'low': [95] * 50,
        'close': [100] * 50,
        'volume': [1000] * 50
    }
    df = pd.DataFrame(data)
    
    # 1. Gösterge hesaplamayı test et
    df = strategy.calculate_indicators(df)
    print("✅ Göstergeler hesaplandı.")
    assert 'atr' in df.columns
    assert 'vol_ma' in df.columns
    
    # 2. WAIT sinyalini test et (Değişim yok)
    signal = strategy.generate_signal("BTCUSDT", df)
    print(f"🔍 Beklenen WAIT Sinyali: {signal['side']}")
    assert signal['side'] == 'WAIT'
    
    # 3. LONG sinyalini test et (Fiyat ve Hacim artışı)
    # Son mumu %2 yükseliş ve yüksek hacim yapalım
    df.loc[df.index[-1], 'open'] = 100
    df.loc[df.index[-1], 'close'] = 102.5 # %2.5 artış
    df.loc[df.index[-1], 'volume'] = 5000 # Hacim patlaması
    
    # Göstergeleri tekrar hesapla (vol_ma değişebilir ama son mum hacmi kesinlikle MA*1.5 üstünde)
    df = strategy.calculate_indicators(df)
    signal = strategy.generate_signal("BTCUSDT", df)
    
    print(f"🚀 LONG Sinyal Testi: {signal['side']} | Reason: {signal.get('reason')}")
    assert signal['side'] == 'LONG'
    assert 'sl' in signal
    assert 'tp1' in signal
    
    print("\n✨ TÜM STRATEJİ TESTLERİ BAŞARIYLA TAMAMLANDI!")

if __name__ == "__main__":
    try:
        test_strategy()
    except Exception as e:
        print(f"❌ Test başarısız: {e}")
        import traceback
        traceback.print_exc()
