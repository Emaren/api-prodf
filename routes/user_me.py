# routes/user_me.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

from db.db import get_db
from db.models.user import User  # import the modular User model

router = APIRouter(prefix="/api/user", tags=["user"])

# ───────────────────────────────────────────────
# 🔐  Firebase bearer-token dependency (optional)
# ───────────────────────────────────────────────
auth_scheme = HTTPBearer()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate the Firebase ID token and return the DB user."""
    try:
        decoded = auth.verify_id_token(creds.credentials)
        uid = decoded["uid"]
        result = await db.execute(select(User).where(User.uid == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# ───────────────────────────────────────────────
# 🧾  Manual fallback (PWA/offline or dev)
# ───────────────────────────────────────────────
class UserMeRequest(BaseModel):
    uid: str | None = None
    email: str | None = None
    in_game_name: str | None = None

@router.post("/me")
async def get_or_create_user(data: UserMeRequest, db_gen=Depends(get_db)):
    """Return the user if it exists; otherwise create it if enough data is given."""
    print(f"🔎 /me request: {data}")

    async with db_gen as db:
        # 1️⃣  Try finding user by UID or email
        user = None
        if data.uid:
            res = await db.execute(select(User).where(User.uid == data.uid))
            user = res.scalar_one_or_none()

        if not user and data.email:
            res = await db.execute(select(User).where(User.email == data.email))
            user = res.scalar_one_or_none()

        if user:
            return user.to_dict()        # ✅ includes `is_admin`

        # 2️⃣  If user not found, create one (requires all fields)
        if not (data.uid and data.email and data.in_game_name):
            raise HTTPException(status_code=404, detail="User not found and insufficient data to create.")

        # Determine whether this is the very first user
        count_res = await db.execute(select(func.count()).select_from(User))
        user_count: int = count_res.scalar()
        is_admin = user_count == 0       # ✅ first user becomes admin

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

        print(f"📌 Created user {new_user.uid} — is_admin={new_user.is_admin}")
        return new_user.to_dict()        # ✅ includes `is_admin`

__all__ = ["get_current_user"]
