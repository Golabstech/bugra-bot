"""
📡 Bugra-Bot Monitoring API
Northflank üzerinde botun durumunu izlemek için
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import io
import csv
import json
from bot.redis_client import redis_client
from bot.config import LOG_LEVEL

app = FastAPI(title="Bugra-Bot API", version="3.0.0")

# --- Replay Modelleri ---
class ReplayStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class ReplayConfig(BaseModel):
    start_date: str = Field(..., description="Başlangıç tarihi (YYYY-MM-DD)")
    end_date: str = Field(..., description="Bitiş tarihi (YYYY-MM-DD)")
    speed: float = Field(100.0, description="Hız çarpanı (1.0 = gerçek zaman)")
    symbols: List[str] = Field([], description="Test edilecek coinler (boş = tümü)")
    initial_balance: float = Field(10000.0, description="Başlangıç bakiyesi")
    
class ReplayState(BaseModel):
    status: ReplayStatus
    current_time: Optional[str] = None
    progress_pct: float = 0.0
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    speed: float = 100.0
    symbols_tested: int = 0
    trades_executed: int = 0
    final_balance: Optional[float] = None

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
async def get_trades(symbol: Optional[str] = None, full: bool = False, limit: int = 50):
    """Borsadaki işlem geçmişini getir. full=true ise tüm geçmişi derinlemesine tarar."""
    from bot.exchange import ExchangeClient
    exchange = ExchangeClient()
    
    if symbol:
        return exchange.fetch_trade_history(symbol, limit=limit)
    
    if full:
        return exchange.fetch_all_trade_history(limit_per_symbol=limit)
    
    # Varsayılan: Aktif ve adayları tara
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
async def download_trades(symbol: Optional[str] = None, full: bool = False):
    """İşlem geçmişini CSV olarak indir. full=true ise tüm geçmişi derinlemesine tarar."""
    from bot.exchange import ExchangeClient
    exchange = ExchangeClient()
    
    all_trades = []
    if symbol:
        all_trades = exchange.fetch_trade_history(symbol, limit=200)
    elif full:
        all_trades = exchange.fetch_all_trade_history(limit_per_symbol=200)
    else:
        # Mevcut akıllı tarama (Aktif + Adaylar)
        positions = await redis_client.hgetall("bot:positions")
        target_symbols = list(positions.keys())
        candidates = await redis_client.get("bot:candidates") or []
        for c in candidates[:20]:
            if c['symbol'] not in target_symbols: target_symbols.append(c['symbol'])
            
        for sym in target_symbols:
            trades = exchange.fetch_trade_history(sym, limit=100)
            if trades: all_trades.extend(trades)
    
    if not all_trades:
        raise HTTPException(status_code=404, detail="İşlem geçmişi bulunamadı.")
    
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

# --- Replay Mode Endpoints ---

@app.get("/replay/status", response_model=ReplayState)
async def get_replay_status():
    """Replay modunun mevcut durumunu getir"""
    state = await redis_client.get("replay:state")
    if not state:
        return ReplayState(status=ReplayStatus.IDLE)
    return ReplayState(**state)

@app.post("/replay/start")
async def start_replay(config: ReplayConfig, background_tasks: BackgroundTasks):
    """
    Replay modunu başlat
    
    Örnek:
    ```json
    {
        "start_date": "2026-01-15",
        "end_date": "2026-01-16",
        "speed": 1000,
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "initial_balance": 10000
    }
    ```
    """
    # Mevcut durumu kontrol et
    current = await redis_client.get("replay:state")
    if current and current.get("status") == ReplayStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Replay zaten çalışıyor")
    
    # Replay konfigürasyonunu Redis'e kaydet
    replay_config = {
        "status": ReplayStatus.RUNNING,
        "start_date": config.start_date,
        "end_date": config.end_date,
        "speed": config.speed,
        "symbols": config.symbols,
        "initial_balance": config.initial_balance,
        "current_time": config.start_date,
        "progress_pct": 0.0,
        "trades_executed": 0,
        "started_at": datetime.now().isoformat()
    }
    
    await redis_client.set("replay:state", replay_config)
    await redis_client.set("replay:command", {"action": "start", "config": config.dict()})
    
    return {
        "status": "started",
        "message": f"Replay başlatıldı: {config.start_date} → {config.end_date} @ {config.speed}x",
        "config": config
    }

@app.post("/replay/stop")
async def stop_replay():
    """Replay modunu durdur"""
    await redis_client.set("replay:command", {"action": "stop"})
    
    state = await redis_client.get("replay:state") or {}
    state["status"] = ReplayStatus.IDLE
    await redis_client.set("replay:state", state)
    
    return {"status": "stopped", "message": "Replay durduruldu"}

@app.post("/replay/pause")
async def pause_replay():
    """Replay modunu duraklat"""
    await redis_client.set("replay:command", {"action": "pause"})
    
    state = await redis_client.get("replay:state") or {}
    state["status"] = ReplayStatus.PAUSED
    await redis_client.set("replay:state", state)
    
    return {"status": "paused", "message": "Replay duraklatıldı"}

@app.post("/replay/resume")
async def resume_replay():
    """Replay modunu devam ettir"""
    await redis_client.set("replay:command", {"action": "resume"})
    
    state = await redis_client.get("replay:state") or {}
    state["status"] = ReplayStatus.RUNNING
    await redis_client.set("replay:state", state)
    
    return {"status": "resumed", "message": "Replay devam ediyor"}

@app.get("/replay/available-symbols")
async def get_available_symbols():
    """Replay için kullanılabilir coinleri listele"""
    import os
    from bot.config import REPLAY_DATA_FOLDER
    
    symbols = []
    if os.path.exists(REPLAY_DATA_FOLDER):
        for f in os.listdir(REPLAY_DATA_FOLDER):
            if f.endswith('_USDT_USDT.csv') and not f.startswith('_'):
                coin = f.replace('_USDT_USDT.csv', '')
                symbols.append(f"{coin}USDT")
    
    return {
        "count": len(symbols),
        "symbols": sorted(symbols)
    }
