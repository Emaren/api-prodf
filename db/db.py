import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from fastapi import Depends

# Load models dynamically in init_db_async to avoid circular imports
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aoe2user:secretpassword@localhost:5432/aoe2db"
)

# Create async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ───────────────────────────────────────────────
# 🛠 Async DB init
# ───────────────────────────────────────────────
async def init_db_async():
    """Create all tables using the declarative Base from models.py."""
    try:
        from db.models import Base  # Delayed import to avoid circular dependency
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("✅ Async tables created.")
    except Exception as e:
        logging.error(f"❌ Failed to initialize DB async: {e}")
        raise

# ───────────────────────────────────────────────
# 🧠 Async query helpers
# ───────────────────────────────────────────────
async def get_user_by_uid(uid: str):
    """Query user by UID (string, not integer ID)."""
    from db.models import User
    async with async_session() as session:
        result = await session.execute(
            User.__table__.select().where(User.uid == uid)
        )
        return result.scalar_one_or_none()

async def get_user_by_email(email: str):
    from db.models import User
    async with async_session() as session:
        result = await session.execute(
            User.__table__.select().where(User.email == email)
        )
        return result.scalar_one_or_none()

@asynccontextmanager
async def get_db():
    async with async_session() as session:
        yield session