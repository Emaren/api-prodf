#!/usr/bin/env bash
# go to the repo root (where app.py lives)
cd "$(dirname "$0")"
# activate the venv
source "$(dirname "$0")/venv/bin/activate"
# exec Uvicorn so PM2 can track it directly
exec uvicorn app:app --host 0.0.0.0 --port 8002
