#!/bin/sh
set -e

echo "=== Running database migrations ==="
alembic upgrade head

echo "=== Starting Peat CRM Application (FastAPI + Telegram Bot) ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
