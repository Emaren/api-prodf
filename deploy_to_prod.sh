#!/bin/bash

# Load env vars from .env or export manually
PROD_DB_PASS="GvoxmmKHfCMOKVKBkpx6c1mQrQZ5hHHN"
PROD_DB_URL="postgresql+asyncpg://aoe2hd_db_user@dpg-cvo1fgeuk2gs73bgj3eg-a.oregon-postgres.render.com:5432/aoe2hd_db"

echo "🚀 Deploying migrations to production..."

PGPASSWORD="$PROD_DB_PASS" alembic -x db_url="$PROD_DB_URL" upgrade head

echo "✅ Production schema updated successfully!"
