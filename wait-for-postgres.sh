#!/bin/sh
set -e

echo "⏳ Waiting for Postgres using DATABASE_URL..."

until pg_isready -d "$DATABASE_URL" > /dev/null 2>&1; do
  echo "❌ Postgres is unavailable - sleeping"
  sleep 2
done

echo "✅ Postgres is up - launching app"
exec python app.py
