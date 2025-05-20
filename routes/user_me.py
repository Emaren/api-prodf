# routes/user_me.py

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

from db.db import get_db
from db.models.user import User

router = APIRouter(prefix="/api/user", tags=["user"])

# ───────────────────────────────────────────────
# 🔐 Firebase bearer-token dependency
# ───────────────────────────────────────────────
auth_scheme = HTTPBearer()

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate the Firebase ID token and return the DB user."""
    try:
        token = creds.credentials
        print(f"🔐 Bearer token received: {token[:20]}...")

        decoded = auth.verify_id_token(token)
        uid = decoded["uid"]
        email = decoded.get("email", "unknown")
        print(f"✅ Firebase decoded UID: {uid}, email: {email}")

        result = await db.execute(select(User).where(User.uid == uid))
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ No user found in DB for UID: {uid}")
            raise HTTPException(status_code=404, detail="User not found")

        print(f"✅ User found: {user.uid}")
        return user
    except Exception as e:
        print(f"❌ Firebase token validation failed: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# ───────────────────────────────────────────────
# 🧾 Manual fallback: for dev, offline mode, or initial registration
# ───────────────────────────────────────────────
class UserMeRequest(BaseModel):
    uid: str | None = None
    email: str | None = None
    in_game_name: str | None = None

@router.post("/me")
async def get_or_create_user(data: UserMeRequest, db_gen=Depends(get_db)):
    print(f"📥 POST /me — Payload: {data}")

    try:
        async with db_gen as db:
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

            # Not found — check if enough info is provided to create one
            if not (data.uid and data.email and data.in_game_name):
                print("⚠️ Missing data — can't create user")
                raise HTTPException(status_code=404, detail="User not found and insufficient data to create.")

            # Count existing users
            count_res = await db.execute(select(func.count()).select_from(User))
            user_count: int = count_res.scalar()
            is_admin = user_count == 0

            # Create new user
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
