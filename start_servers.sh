#!/bin/bash

# iM-System Unified Startup Script

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "------------------------------------------------"
echo "🚀 iM-System: Starting Backend & Frontend..."
echo "------------------------------------------------"

# 1. Kill existing processes (Backend and Frontend)
echo "🧹 Cleaning up old processes..."
pkill -f "uvicorn main:app" > /dev/null 2>&1
pkill -f "vite" > /dev/null 2>&1
sleep 1

# 2. Start Backend
echo "📡 Starting Backend (FastAPI)..."
cd backend
if [ -d "../venv" ]; then
    source ../venv/bin/activate
    echo "🐍 Virtual environment activated."
else
    echo "⚠️  Warning: venv not found. Trying to run with system python."
fi

# Run in background and redirect output to log file
nohup uvicorn main:app --host 0.0.0.0 --port 5656 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID) - Logs: backend/backend.log"
cd ..

# 3. Start Frontend
echo "💻 Starting Frontend (Vite)..."
cd frontend
# Run in background and redirect output to log file
nohup npm run dev -- --host 0.0.0.0 --port 3000 > vite.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID) - Logs: frontend/vite.log"
cd ..

echo "------------------------------------------------"
echo "🌐 iM-System is now running!"
echo "📍 Backend:  http://localhost:5656"
echo "📍 Frontend: http://localhost:3000"
echo "------------------------------------------------"
echo "Check logs with:"
echo "tail -f backend/backend.log"
echo "tail -f frontend/vite.log"
