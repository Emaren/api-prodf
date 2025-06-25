# routes/user_me.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from db.models import User
from dependencies.auth import get_firebase_user

router = APIRouter(tags=["user"])

# 🔑 Dependency to retrieve current logged-in user
async def get_current_user(
    credentials: dict = Depends(get_firebase_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    uid = credentials.get("uid")
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    result = await db.execute(select(User).where(User.uid == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# 🔧 Main /me route, now returning is_admin
@router.get("/me")
async def get_user_me(user: User = Depends(get_current_user)):
    return {
        "uid": user.uid,
        "email": user.email,
        "in_game_name": user.in_game_name,
        "verified": user.verified,
        "created_at": user.created_at,
        "last_seen": user.last_seen,
        "is_admin": user.is_admin  # <-- 🔥 critical fix
    }
