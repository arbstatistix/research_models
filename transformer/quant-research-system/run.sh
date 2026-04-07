#!/bin/bash

# Quant Research Pipeline - Start Backend & Frontend

set -e

PROJECT_ROOT="/home/mate/Desktop/adaptive_scraper/research_models/transformer/quant-research-system"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "========================================"
echo "  Quant Research Pipeline"
echo "========================================"
echo ""

# Kill any existing processes on ports
echo "🔍 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
sleep 1
echo "✓ Ports cleared"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠ Warning: Ollama doesn't appear to be running"
    echo "  Start it with: ollama serve"
    echo ""
fi

# Start Backend
echo "🚀 Starting Backend..."
cd "$BACKEND_DIR"

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null

python run.py &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "  Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ Backend ready at http://localhost:8000"
        break
    fi
    sleep 1
done

# Start Frontend
echo ""
echo "🚀 Starting Frontend..."
cd "$FRONTEND_DIR"

if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# Wait for frontend
sleep 3
echo "  ✓ Frontend ready at http://localhost:5173"

echo ""
echo "========================================"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -P $$ 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

# Wait for either process to exit
wait
