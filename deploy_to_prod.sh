#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")"

# 🛠️ Production DB credentials (render.com managed DB)
PROD_DB_PASS="GvoxmmKHfCMOKVKBkpx6c1mQrQZ5hHHN"
PROD_DB_URL="postgresql+asyncpg://aoe2hd_db_user@dpg-cvo1fgeuk2gs73bgj3eg-a.oregon-postgres.render.com:5432/aoe2hd_db"

# Ensure relative imports resolve correctly
export PYTHONPATH=$(pwd)
export ENV=production

echo "🚀 Applying Alembic migrations to production database..."

PGPASSWORD="$PROD_DB_PASS" \
alembic -x db_url="$PROD_DB_URL" upgrade head

echo "✅ Production schema updated successfully!"
