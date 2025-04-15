import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from fastapi import Depends

# ------------------------------------------------------------------------
# 🗄️ Set the fallback DB URI here (not secure, for demonstration only!)
# This code will use an environment variable "DATABASE_URL" if present.
# Otherwise, it falls back to this literal connection string with user/pass.
# ------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aoe2user:secretpassword@localhost:5432/aoe2d?sslmode=require"
)

# ------------------------------------------------------------------------
# 🚀 Create the async engine and sessionmaker
# ------------------------------------------------------------------------
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ------------------------------------------------------------------------
# 🏗️ Initialize DB and create tables
# ------------------------------------------------------------------------
async def init_db_async():
    """
    Create all tables using the declarative Base from models.py.
    """
    try:
        from db.models import Base  # Avoid circular import issues
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("✅ Async tables created.")
    except Exception as e:
        logging.error(f"❌ Failed to initialize DB async: {e}")
        raise

# ------------------------------------------------------------------------
# 🧩 Provide an async DB session for FastAPI dependencies
# ------------------------------------------------------------------------
@asynccontextmanager
async def get_db():
    async with async_session() as session:
        yield session

# ------------------------------------------------------------------------
# 🏷️ Example helper methods for queries
# ------------------------------------------------------------------------
async def get_user_by_uid(uid: str):
    """
    Retrieve a user by their unique string UID.
    """
    from db.models import User
    async with async_session() as session:
        result = await session.execute(User.__table__.select().where(User.uid == uid))
        return result.scalar_one_or_none()

async def get_user_by_email(email: str):
    """
    Retrieve a user by their email address.
    """
    from db.models import User
    async with async_session() as session:
        result = await session.execute(User.__table__.select().where(User.email == email))
        return result.scalar_one_or_none()
