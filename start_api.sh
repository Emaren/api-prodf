#!/usr/bin/env bash

# ────────────────────────────────────────────────────────────────────────
# 🚀 FastAPI Launcher for Local Development (w/ Firebase + Debug Logs)
# ────────────────────────────────────────────────────────────────────────

# ⛳️ Always run from the script's directory (repo root)
cd "$(dirname "$0")"

# 🧬 Load .env if it exists
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

# 🔐 Firebase Admin SDK key override (ensure it points to a valid file)
export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-./secrets/serviceAccountKey.json}"

# ✅ Optional Firebase project ID override
# export FIREBASE_PROJECT_ID="aoe2hd"

# ✅ Explicit DATABASE_URL fallback (for local dev)
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://aoe2user:secretpassword@localhost:5433/aoe2db}"

# 📣 Set logging level for FastAPI + Uvicorn
export LOG_LEVEL="${LOG_LEVEL:-debug}"

# 🐍 Activate venv if needed
source ./venv/bin/activate

# 💥 Fire it up!
exec uvicorn app:app \
  --host 0.0.0.0 \
  --port 8002 \
  --reload \
  --log-level "$LOG_LEVEL"

