#!/bin/bash
cd /var/www/aoe2hdbets-api/aoe2hd-parsing || exit 1
source .env.dbs

# ───────────────────────────────────────────────
# 🔥 Firebase / Firestore Auth
# ───────────────────────────────────────────────
firebase auth:export users.json --format=json > /dev/null
firebase_count=$(jq '.users | length' users.json)

echo "🔥 Firebase Auth Users"
echo "----------------------"
echo "📥 Firebase users:  $firebase_count"
if [ "$firebase_count" -gt 0 ]; then
  jq -r '.users[].email' users.json | sed 's/^/   - /'
else
  echo "   No Firebase users found."
fi
echo ""

# ───────────────────────────────────────────────
# 🐘 Local Postgres (localhost)
# ───────────────────────────────────────────────
local_count=$(psql -h localhost -U aoe2user -d aoe2db -tAc "SELECT COUNT(*) FROM users;")

echo "🐘 Local Postgres Users"
echo "-----------------------"
echo "📊 Local DB users: $local_count"
if [ "$local_count" -gt 0 ]; then
  psql -h localhost -U aoe2user -d aoe2db -P pager=off -c \
    "SELECT email, in_game_name, CASE WHEN is_admin THEN '✅ admin' ELSE '❌' END AS role FROM users;" \
    | sed '1d;$d' | sed 's/^/   - /'
else
  echo "   No local Postgres users found."
fi
echo ""

# ───────────────────────────────────────────────
# ☁️ Production Postgres (Render)
# ───────────────────────────────────────────────
render_count=$(psql "$RENDER_DB_URI" -tAc "SELECT COUNT(*) FROM users;")

echo "☁️ Render (Prod) Postgres Users"
echo "-------------------------------"
echo "📊 Prod DB users: $render_count"
if [ "$render_count" -gt 0 ]; then
  psql "$RENDER_DB_URI" -P pager=off -c \
    "SELECT email, in_game_name, CASE WHEN is_admin THEN '✅ admin' ELSE '❌' END AS role FROM users;" \
    | sed '1d;$d' | sed 's/^/   - /'
else
  echo "   No Render Postgres users found."
fi
