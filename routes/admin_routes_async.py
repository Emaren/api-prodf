from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import User
from db.db import get_async_session
from datetime import datetime
import os

router = APIRouter(prefix="/api/admin", tags=["Admin"])

def verify_admin_token(authorization: str = Header(...)):
    expected_token = f"Bearer {os.getenv('ADMIN_TOKEN', 'secretadmin')}"
    if authorization != expected_token:
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.get("/users")
async def list_users(
    authorization: str = Header(...),
    session: AsyncSession = Depends(get_async_session)
):
    verify_admin_token(authorization)

    result = await session.execute(select(User))
    users = result.scalars().all()

    return [u.to_dict() for u in users]

@router.post("/user/online")
async def mark_user_online(
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_async_session)
):
    uid = payload.get("uid")
    if not uid:
        raise HTTPException(status_code=400, detail="Missing UID")

    result = await session.execute(select(User).where(User.uid == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.last_seen = datetime.utcnow()
    await session.commit()
    return {"message": "User marked online", "last_seen": user.last_seen.isoformat()}
