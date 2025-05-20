#!/bin/bash

# Must be run from aoe2hd-parsing
if [ "$(basename "$PWD")" != "aoe2hd-parsing" ]; then
  echo "❌ Please run this script from inside the aoe2hd-parsing directory."
  exit 1
fi

# 1. Git push
echo "📦 Git pushing code to main branch..."
git add .
git commit -m "🚀 Prod deploy"
git push origin main

# 2. Alembic migration
echo "🛠️ Applying Alembic migrations to Render database..."
export ENV=production
set -a
source .env.production
set +a
export PYTHONPATH=$(pwd)
alembic upgrade head
echo "✅ Alembic migrations applied successfully!"

# 3. Vercel deploy
echo "🚀 Triggering Vercel frontend deploy..."
VERCEL_DEPLOY_HOOK="https://api.vercel.com/v1/integrations/deploy/REPLACE_THIS_WITH_YOUR_HOOK"
curl -X POST "$VERCEL_DEPLOY_HOOK"
echo "✅ Vercel frontend deployment triggered!"

echo "🎉 All systems go. Prod deploy complete."
