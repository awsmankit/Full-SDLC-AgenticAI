#!/bin/bash
echo "🚀 Starting Multi-Agent QA System UI..."

# Start Backend
echo "Starting Backend (Port 8000)..."
uv run uvicorn src.api.server:app --reload --port 8000 &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend (Port 3000)..."
cd ui
npm run dev &
FRONTEND_PID=$!

echo "✅ System is running!"
echo "👉 Open http://localhost:3000 in your browser"
echo "Press CTRL+C to stop everything."

# Wait for process
wait $BACKEND_PID $FRONTEND_PID
