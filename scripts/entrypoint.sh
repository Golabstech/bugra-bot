#!/bin/bash
set -e

echo "🚀 Bugra-Bot Başlatılıyor — Rol: ${BOT_ROLE:-worker}"

if [ "$BOT_ROLE" = "api" ]; then
    echo "📡 Monitoring API (Uvicorn) başlatılıyor..."
    exec uvicorn api.main:app --host 0.0.0.0 --port 8000
else
    echo "🧠 Redis Server (Background) başlatılıyor..."
    redis-server --daemonize yes --protected-mode no
    
    echo "🤖 Trading Worker başlatılıyor..."
    exec python -m bot.main
fi
