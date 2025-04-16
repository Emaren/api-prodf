import sys
import os
import asyncio
import json
import pathlib
from logging.config import fileConfig

# ✅ Fix module import path early
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from db.models import Base  # your declarative_base

# ─────────────────────────────────────────────
# 📦 Load config and DB URL
# ─────────────────────────────────────────────
CONFIG_PATH = pathlib.Path(__file__).parent.parent / "config.json"
if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        DB_URL = json.load(f).get("DATABASE_URL")
else:
    # Fallback: environment variable, then a local default
    DB_URL = os.getenv("DATABASE_URL") or "postgresql+asyncpg://aoe2user:postgres@localhost:5432/aoe2db"

# ─────────────────────────────────────────────
# 🔧 Alembic config
# ─────────────────────────────────────────────
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

# 🚀 Offline migrations
def run_migrations_offline():
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

# 🏗 Online migrations (async)
def do_run_migrations(sync_connection):
    context.configure(
        connection=sync_connection,
        target_metadata=target_metadata,
    )
    context.run_migrations()

async def run_migrations_online():
    connectable: AsyncEngine = create_async_engine(DB_URL, future=True)
    async with connectable.begin() as conn:
        await conn.run_sync(do_run_migrations)

def run_async():
    asyncio.run(run_migrations_online())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_async()
