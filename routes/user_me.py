# routes/user_me.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from db.models.user import User
from utils.auth_utils import get_current_user  # ✅ Use shared utility

router = APIRouter(prefix="/api/user", tags=["user"])

# ───────────────────────────────────────────────
# 🧾 Manual fallback: for dev, offline mode, or initial registration
# ───────────────────────────────────────────────
class UserMeRequest(BaseModel):
    uid: str | None = None
    email: str | None = None
    in_game_name: str | None = None

@router.post("/me")
async def get_or_create_user(data: UserMeRequest, db: AsyncSession = Depends(get_db)):
    print(f"📥 POST /me — Payload: {data}")
    try:
        # Try finding user by UID
        if data.uid:
            res = await db.execute(select(User).where(User.uid == data.uid))
            user = res.scalar_one_or_none()
            if user:
                print(f"✅ Found by UID: {user.uid}")
                return user.to_dict()

        # Try finding user by email
        if data.email:
            res = await db.execute(select(User).where(User.email == data.email))
            user = res.scalar_one_or_none()
            if user:
                print(f"✅ Found by email: {user.email}")
                return user.to_dict()

        if not (data.uid and data.email and data.in_game_name):
            print("⚠️ Missing data — can't create user")
            raise HTTPException(status_code=404, detail="User not found and insufficient data to create.")

        count_res = await db.execute(select(func.count()).select_from(User))
        user_count = count_res.scalar()
        is_admin = user_count == 0

        new_user = User(
            uid=data.uid,
            email=data.email,
            in_game_name=data.in_game_name,
            verified=False,
            is_admin=is_admin,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        print(f"🆕 Created user {new_user.uid} | admin: {is_admin}")
        return new_user.to_dict()

    except Exception as e:
        print(f"🔥 Unhandled error in /me route: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
