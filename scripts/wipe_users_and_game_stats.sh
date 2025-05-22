#!/bin/bash
set -e

echo "🔍 Checking user counts BEFORE wipe..."
./scripts/check_all_users.sh
echo

read -p "⚠️ Are you sure you want to DELETE ALL users from Firebase and Postgres? (y/n): " confirm
[[ $confirm == [yY] ]] || exit 1

echo "🔥 Deleting all Firebase Auth users..."
python scripts/delete_firebase_users.py

echo "🧹 Truncating PostgreSQL users table (cascades to game_stats)..."
psql -U aoe2user -d aoe2db -h localhost -c "TRUNCATE TABLE users RESTART IDENTITY CASCADE;"

echo
echo "🔁 Checking user counts AFTER wipe..."
./scripts/check_all_users.sh

echo
echo "✅ All users deleted from Firebase and Postgres."
