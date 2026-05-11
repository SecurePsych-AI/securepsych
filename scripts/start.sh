#!/usr/bin/env bash
# start.sh — Start all SecurePsych services locally (dev, no Docker required)
#
# Prerequisites:
#   - backend/.venv activated Python environment (run scripts/setup_backend_dev_env.py first)
#   - Ollama running at http://localhost:11434
#   - Each service's .env file populated (see backend/{service}/.env.example)
#
# Usage: bash scripts/start.sh

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/backend/.venv"
UVICORN="$VENV/bin/uvicorn"
LOG_DIR="/tmp/securepsych"

if [ ! -f "$UVICORN" ]; then
    echo "[ERROR] Python venv not found at $VENV"
    echo "        Run: python scripts/setup_backend_dev_env.py"
    exit 1
fi

mkdir -p "$LOG_DIR"

# Detect encrypted volume; bypass FERPA path check in dev if not mounted
if [ -d "/mnt/securepsych" ] || [ -d "/Volumes/securepsych" ]; then
    export SECUREPSYCH_ENV=production
    echo "[SecurePsych] Encrypted volume detected — production mode."
else
    export SECUREPSYCH_ENV=test
    echo "[WARNING] Encrypted volume not found. Running in DEVELOPMENT mode."
    echo "[WARNING] Do NOT use with real student data in this mode."
fi

# PYTHONPATH must include the project root so backend.shared.* imports resolve
export PYTHONPATH="$ROOT"

echo ""
echo "[SecurePsych] Starting services..."

# Gateway (port 8000) — uses flat imports, must run from its own directory
(cd "$ROOT/backend/gateway" && "$UVICORN" main:app \
    --host 127.0.0.1 --port 8000 --log-level info \
    > "$LOG_DIR/gateway.log" 2>&1) &
GATEWAY_PID=$!

# RAG service (port 8001)
(cd "$ROOT/backend/rag" && "$UVICORN" api:app \
    --host 127.0.0.1 --port 8001 --log-level info \
    > "$LOG_DIR/rag.log" 2>&1) &
RAG_PID=$!

# Summarizer service (port 8002)
(cd "$ROOT/backend/summarizer" && "$UVICORN" main:app \
    --host 127.0.0.1 --port 8002 --log-level info \
    > "$LOG_DIR/summarizer.log" 2>&1) &
SUMMARIZER_PID=$!

# Jargon service (port 8003)
(cd "$ROOT/backend/jargon" && "$UVICORN" main:app \
    --host 127.0.0.1 --port 8003 --log-level info \
    > "$LOG_DIR/jargon.log" 2>&1) &
JARGON_PID=$!

# Frontend dev server (port 5173)
(cd "$ROOT/frontend" && npm run dev \
    > "$LOG_DIR/frontend.log" 2>&1) &
FRONTEND_PID=$!

echo ""
echo "  Gateway     http://localhost:8000   (log: $LOG_DIR/gateway.log)"
echo "  RAG         http://localhost:8001   (log: $LOG_DIR/rag.log)"
echo "  Summarizer  http://localhost:8002   (log: $LOG_DIR/summarizer.log)"
echo "  Jargon      http://localhost:8003   (log: $LOG_DIR/jargon.log)"
echo "  Frontend    http://localhost:5173   (log: $LOG_DIR/frontend.log)"
echo ""
echo "[SecurePsych] All services started. PIDs: gateway=$GATEWAY_PID rag=$RAG_PID summarizer=$SUMMARIZER_PID jargon=$JARGON_PID frontend=$FRONTEND_PID"
echo "To stop: bash scripts/stop.sh"
echo "To tail logs: tail -f $LOG_DIR/*.log"
