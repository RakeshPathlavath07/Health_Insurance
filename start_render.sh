#!/bin/bash
set -e

PORT="${PORT:-8000}"
echo "=== STARTING FASTAPI BACKEND ON PORT ${PORT} ==="
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT}"
