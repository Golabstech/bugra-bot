"""
📡 Bugra-Bot Monitoring API
Northflank üzerinde botun durumunu izlemek için
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import io
import csv
from bot.redis_client import redis_client
from bot.config import LOG_LEVEL

app = FastAPI(title="Bugra-Bot API", version="3.0.0")

# --- Modeller ---
class PositionModel(BaseModel):
    symbol: str
    side: str
    entry_price: float
    amount: float
    margin: float
    pnl_pct: Optional[float] = 0
    opened_at: str

class StatsModel(BaseModel):
    balance: float
    open_positions: int
    daily_pnl: float
    wins: int
    losses: int
    last_update: str

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Northflank Health Check"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/stats", response_model=StatsModel)
async def get_stats():
    """Genel bot istatistiklerini getir"""
    stats = await redis_client.get("bot:stats")
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    return stats

@app.get("/positions", response_model=List[dict])
async def get_positions():
    """Aktif pozisyonları getir"""
    positions = await redis_client.hgetall("bot:positions")
    return list(positions.values())

@app.get("/candidates", response_model=List[dict])
async def get_candidates():
    """Scanner verilerini getir"""
    candidates = await redis_client.get("bot:candidates")
    return candidates or []

@app.get("/trades")
async def get_trades(symbol: Optional[str] = None, limit: int = 50):
    """Borsadaki işlem geçmişini getir. Sembol verilmezse aktif pozisyonları tarar."""
    from bot.exchange import ExchangeClient
    exchange = ExchangeClient()
    
    if symbol:
        return exchange.fetch_trade_history(symbol, limit=limit)
    
    # Sembol verilmediyse aktif ve adayları tara
    positions = await redis_client.hgetall("bot:positions")
    candidates = await redis_client.get("bot:candidates") or []
    
    target_symbols = list(positions.keys())
    for c in candidates[:10]: # İlk 10 adayı ekle
        if c['symbol'] not in target_symbols:
            target_symbols.append(c['symbol'])
            
    all_trades = []
    for sym in target_symbols:
        trades = exchange.fetch_trade_history(sym, limit=20)
        if trades:
            all_trades.extend(trades)
            
    # Zamana göre sırala (en yeni üstte)
    all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    return all_trades[:limit]

@app.get("/download-trades")
async def download_trades(symbol: Optional[str] = None):
    """İşlem geçmişini CSV olarak indir. Sembol verilmezse geniş tarama yapar."""
    from bot.exchange import ExchangeClient
    exchange = ExchangeClient()
    
    target_symbols = []
    if symbol:
        target_symbols = [symbol]
    else:
        # Geniş tarama: Aktifler + Adaylar + Bakiyeli Coinler
        positions = await redis_client.hgetall("bot:positions")
        target_symbols = list(positions.keys())
        
        candidates = await redis_client.get("bot:candidates") or []
        for c in candidates[:20]:
            if c['symbol'] not in target_symbols: target_symbols.append(c['symbol'])
            
    if not target_symbols:
        raise HTTPException(status_code=404, detail="Taranacak sembol bulunamadı. Lütfen bir sembol belirtin.")

    all_trades = []
    for sym in target_symbols:
        trades = exchange.fetch_trade_history(sym, limit=100)
        if trades: all_trades.extend(trades)
    
    if not all_trades:
        raise HTTPException(status_code=404, detail="Belirtilen coinler için işlem geçmişi bulunamadı.")
    
    # Sırala
    all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    output = io.StringIO()
    # Excel'de düzgün açılması için noktali virgül (;) kullanıyoruz
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Zaman', 'Sembol', 'Yön', 'Miktar', 'Fiyat', 'Toplam Tutar', 'Komisyon', 'Birim'])
    
    for t in all_trades:
        if not isinstance(t, dict): continue
        writer.writerow([
            t.get('datetime'),
            t.get('symbol'),
            t.get('side'),
            t.get('amount'),
            t.get('price'),
            t.get('cost'),
            t.get('fee', {}).get('cost') if t.get('fee') else 0,
            t.get('fee', {}).get('currency') if t.get('fee') else ''
        ])
    
    # Excel'in Türkçe karakterleri ve tablo yapısını tanıması için UTF-8-SIG (BOM) kullanıyoruz
    csv_data = output.getvalue().encode('utf-8-sig')
    filename = f"bugra_bot_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        io.BytesIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/reset")
async def reset_stats():
    """İstatistikleri sıfırla (Gelişmiş kontrol için)"""
    await redis_client.delete("bot:stats")
    return {"status": "reset requested"}
