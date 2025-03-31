#!/bin/sh
set -e

echo "⏳ Waiting for Postgres at aoe2-postgres:5432..."

# Explicitly specify the target database to avoid "database 'aoe2user' does not exist" errors
until pg_isready -h aoe2-postgres -p 5432 -U aoe2user -d aoe2db > /dev/null 2>&1; do
  echo "❌ Postgres is unavailable - sleeping"
  sleep 2
done

echo "✅ Postgres is up - launching app"
exec python app.py
