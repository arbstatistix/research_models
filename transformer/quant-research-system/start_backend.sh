#!/bin/bash

# Start Backend Server with Port Conflict Resolution

set -e

PROJECT_ROOT="/home/mate/Desktop/adaptive_scraper/research_models/transformer/quant-research-system"
BACKEND_DIR="$PROJECT_ROOT/backend"
PID_FILE="/tmp/quant_research_backend.pid"

echo "========================================"
echo "  Quant Research Backend Starter"
echo "========================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
}
trap cleanup EXIT

# Kill any existing processes on port 8000
echo "🔍 Checking for existing backend processes..."
EXISTING_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$EXISTING_PID" ]; then
    echo "  Found process on port 8000 (PID: $EXISTING_PID), killing..."
    kill -9 $EXISTING_PID 2>/dev/null || true
    sleep 1
    echo "  ✓ Killed existing process"
else
    echo "  ✓ Port 8000 is free"
fi
echo ""

# Change to backend directory
cd "$BACKEND_DIR"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt
echo "  ✓ Dependencies ready"
echo ""

# Save PID to file
echo $$ > "$PID_FILE"

# Start the server
echo "🚀 Starting Backend Server..."
echo "   URL: http://localhost:8000"
echo "   API: http://localhost:8000/api"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

python run.py
