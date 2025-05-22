# routes/user_ping.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from db.db import get_db
from db.models.user import User
from routes.user_me import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])

@router.get("/ping")
async def ping_anonymous():
    return {"status": "ok"}

@router.post("/ping")
async def ping_user(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user.last_seen = datetime.utcnow()
    await db.commit()
    return {"status": "ok"}
