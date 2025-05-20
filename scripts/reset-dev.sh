#!/bin/bash

echo "🧨 Resetting dev environment..."

# 1. Wipe Postgres users table
echo "🧹 Wiping PostgreSQL users table..."
psql -U aoe2user -d aoe2db -h localhost -c "TRUNCATE TABLE users RESTART IDENTITY CASCADE;"

# 2. Wipe Firebase Auth users
echo "🔥 Deleting Firebase Auth users..."
python scripts/delete_firebase_users.py

echo "✅ Dev environment reset complete."
