# routes/user_routes_async.py

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import firebase_admin
from firebase_admin import auth, credentials
from sqlalchemy import desc

from db.db import get_db
from db.models import User, GameStats

router = APIRouter(prefix="/api/user", tags=["user"])

# ——————————————————————————————————————————————————————————
# FIREBASE TOKEN VERIFICATION DEPENDENCY
# ——————————————————————————————————————————————————————————

if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

bearer_scheme = HTTPBearer(auto_error=False)

async def verify_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    try:
        return auth.verify_id_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# ——————————————————————————————————————————————————————————
# 1) The `/me` endpoint
# ——————————————————————————————————————————————————————————

class MeRequest(BaseModel):
    uid: str | None = Field(None, description="Populated from the Firebase token")
    email: str | None = Field(None, description="Populated from the Firebase token")
    in_game_name: str | None = Field(
        None, description="Your AoE2HD username (only required on first-time signup)"
    )

@router.post("/me")
async def me(
    body: MeRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    decoded_token: dict = Depends(verify_firebase_token),
):
    # pull uid/email from Firebase
    body.uid = decoded_token["uid"]
    body.email = decoded_token.get("email")

    # 1) try to find existing user
    result = await db.execute(select(User).where(User.uid == body.uid))
    user = result.scalar_one_or_none()

    # 2) create new user if not found
    if not user:
        if not body.in_game_name:
            raise HTTPException(status_code=400, detail="First-time users must supply in_game_name")

        # determine admin status
        result = await db.execute(select(User).limit(1))
        first_user = result.scalar_one_or_none()
        is_admin = first_user is None

        print(f"[CREATE USER] {body.email} — Admin: {is_admin}")

        user = User(
            uid=body.uid,
            email=body.email,
            in_game_name=body.in_game_name,
            verified=False,
            is_admin=is_admin,
        )

        db.add(user)  # ✅ this line was missing

        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=400, detail="In-game name already taken")

    # 3) return the record
    return {
        "id": user.id,
        "uid": user.uid,
        "email": user.email,
        "in_game_name": user.in_game_name,
        "verified": user.verified,
        "wallet_address": user.wallet_address,
        "is_admin": user.is_admin,
    }


# ——————————————————————————————————————————————————————————
# 2) Existing endpoints
# ——————————————————————————————————————————————————————————

class UpdateNameRequest(BaseModel):
    uid: str
    in_game_name: str

@router.post("/update_name")
async def update_name(
    data: UpdateNameRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.uid == data.uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.in_game_name and user.lock_name:
        raise HTTPException(status_code=403, detail="Name change is locked during a match")
    if user.in_game_name:
        m = await db.execute(
            select(GameStats).filter(
                GameStats.is_final == False,
                GameStats.players.cast(str).ilike(f"%{user.in_game_name}%"),
            )
        )
        if m.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Cannot change name during an active match")

    conflict = await db.execute(
        select(User).where(User.in_game_name == data.in_game_name)
    )
    if conflict.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="That in-game name is already taken")

    user.in_game_name = data.in_game_name
    await db.commit()
    return {"message": "Name updated", "verified": user.verified}


class UpdateWalletRequest(BaseModel):
    uid: str
    wallet_address: str

@router.post("/update_wallet")
async def update_wallet(
    data: UpdateWalletRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.uid == data.uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.wallet_address = data.wallet_address
    await db.commit()
    return {"message": "Wallet updated"}

@router.get("/online")
async def get_online_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .where(User.in_game_name.isnot(None))
        .order_by(desc(User.last_seen))
    )
    users = result.scalars().all()
    return [
        {"uid": u.uid, "in_game_name": u.in_game_name, "verified": u.verified}
        for u in users
    ]

@router.post("/verify_token")
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = credentials.credentials

    result = await db.execute(select(User).where(User.token == token))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "id": user.id,
        "uid": user.uid,
        "email": user.email,
        "in_game_name": user.in_game_name,
        "verified": user.verified,
    }

# ——————————————————————————————————————————————————————————
# 3) Alias: /online_users → /online
# ——————————————————————————————————————————————————————————

@router.get("/online_users")
async def get_online_users_alias(db: AsyncSession = Depends(get_db)):
    return await get_online_users(db)
