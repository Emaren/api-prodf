#!/bin/bash
set -e
source .env.dbs

echo "📤 Dumping schema from LOCAL..."
pg_dump -s --clean -U aoe2user -h localhost -d aoe2db > db/schema.sql

echo "🌐 Syncing schema to VPS Postgres..."
psql -U aoe2user -h 127.0.0.1 -d aoe2db < db/schema.sql

echo "✅ Schema synced to VPS Postgres."
