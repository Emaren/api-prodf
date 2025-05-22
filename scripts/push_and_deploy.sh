#!/bin/bash

# 🧠 Always absolute paths to be safe
BACKEND_DIR="$HOME/projects/aoe2hd-parsing"
FRONTEND_DIR="$HOME/projects/aoe2hd-frontend"

# 1. Git push frontend
echo "🧼 Pushing frontend..."
cd "$FRONTEND_DIR" || exit 1
git add .
git commit -m "🚀 Frontend prod deploy"
git push origin main

# 2. Git push backend
echo "🧼 Pushing backend..."
cd "$BACKEND_DIR" || exit 1
git add .
git commit -m "🚀 Backend prod deploy"
git push origin main

# 3. Alembic DB migration
echo "🛠️ Applying Alembic migrations to Render database..."
export ENV=production
set -a
source "$BACKEND_DIR/.env.production"
set +a
export PYTHONPATH="$BACKEND_DIR"
cd "$BACKEND_DIR" || exit 1
alembic upgrade head
echo "✅ Alembic migrations applied successfully!"

# 4. Trigger Vercel deploy
echo "🚀 Triggering Vercel frontend deploy..."
VERCEL_DEPLOY_HOOK="https://api.vercel.com/v1/integrations/deploy/prj_IzZj1e948vWhj6OespdhkpCRrpNm/AF5gAwABp6"
curl -X POST "$VERCEL_DEPLOY_HOOK"
echo "✅ Vercel frontend deployment triggered!"

echo "🎉 All systems go. Full prod deploy complete."
