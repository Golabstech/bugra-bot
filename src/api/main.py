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
async def get_trades(limit: int = 100):
    """Borsadaki işlem geçmişini JSON olarak getir"""
    from bot.exchange import ExchangeClient
    exchange = ExchangeClient()
    trades = exchange.fetch_trade_history(limit=limit)
    return trades

@app.get("/download-trades")
async def download_trades():
    """İşlem geçmişini CSV dosyası olarak indir"""
    from bot.exchange import ExchangeClient
    exchange = ExchangeClient()
    trades = exchange.fetch_trade_history(limit=500)
    
    if not trades:
        raise HTTPException(status_code=404, detail="İşlem geçmişi bulunamadı.")
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV Başlıkları
    writer.writerow(['Zaman', 'Sembol', 'Yön', 'Fiyat', 'Miktar', 'Tutar', 'Komisyon', 'Birim'])
    
    for t in trades:
        writer.writerow([
            t.get('datetime'),
            t.get('symbol'),
            t.get('side'),
            t.get('price'),
            t.get('amount'),
            t.get('cost'),
            t.get('fee', {}).get('cost') if t.get('fee') else 0,
            t.get('fee', {}).get('currency') if t.get('fee') else ''
        ])
    
    output.seek(0)
    filename = f"bugra_bot_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/reset")
async def reset_stats():
    """İstatistikleri sıfırla (Gelişmiş kontrol için)"""
    await redis_client.delete("bot:stats")
    return {"status": "reset requested"}
