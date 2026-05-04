#!/usr/bin/env bash
# stop.sh — Stop all SecurePsych local dev services

set -e

echo "[SecurePsych] Stopping services..."

pkill -f "uvicorn main:app" 2>/dev/null && echo "  Stopped gateway, summarizer, jargon" || true
pkill -f "uvicorn api:app"  2>/dev/null && echo "  Stopped RAG" || true
pkill -f "vite"             2>/dev/null && echo "  Stopped frontend" || true

echo "[SecurePsych] Done."
