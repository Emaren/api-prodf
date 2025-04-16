import sys
import os
import asyncio
import json
import pathlib
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from db.models import Base  # your declarative_base
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# ✅ Load environment variables from .env
# ─────────────────────────────────────────────
dotenv_path = pathlib.Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# ─────────────────────────────────────────────
# 🔧 Resolve DB URL
# Priority: CLI > .env > config.json > fallback
# ─────────────────────────────────────────────
cli_args = context.get_x_argument(as_dictionary=True)
DB_URL = cli_args.get("db_url")

if not DB_URL:
    config_json_path = pathlib.Path(__file__).parent.parent / "config.json"
    if config_json_path.exists():
        with open(config_json_path) as f:
            DB_URL = json.load(f).get("DATABASE_URL")

DB_URL = DB_URL or os.getenv("DATABASE_URL") or "postgresql+asyncpg://aoe2user:postgres@localhost:5432/aoe2db"

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
