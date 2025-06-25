# routes/user_register.py (🔥 fully patched and prefixed production version)

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

from db.db import get_db
from db.models import User
from db.schemas import UserRegisterRequest
from dependencies.auth import get_firebase_user

# ✅ Set prefix and tag
router = APIRouter(prefix="/api/user", tags=["user"])
logger = logging.getLogger(__name__)

@router.post("/register")
async def register_user(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    firebase_user=Depends(get_firebase_user)
):
    try:
        uid = firebase_user["uid"]
        email = firebase_user.get("email", "").strip()

        if not payload.in_game_name or not payload.in_game_name.strip():
            return JSONResponse(
                status_code=400,
                content={"field": "in_game_name", "error": "In-game name cannot be blank"},
            )

        # 🔍 Check if UID already exists
        result = await db.execute(select(User).where(User.uid == uid))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            logger.info(f"✅ User already exists: {uid}")
            return {"message": "User already exists"}

        # 🔍 Check if in-game name is taken
        name_check = await db.execute(select(User).where(User.in_game_name == payload.in_game_name))
        name_conflict = name_check.scalar_one_or_none()
        if name_conflict:
            return JSONResponse(
                status_code=400,
                content={"field": "in_game_name", "error": "In-game name already taken"},
            )

        # 🥇 First user gets admin rights
        total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
        is_admin = total_users == 0

        new_user = User(
            uid=uid,
            email=email,
            in_game_name=payload.in_game_name,
            is_admin=is_admin,
            verified=False,
            created_at=datetime.utcnow(),
            last_seen=None,
            wallet_address=None,
            lock_name=False,
            token=None,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"✅ Registered new user: {uid} ({email})")
        return {"message": "User registered", "is_admin": is_admin}

    except IntegrityError:
        await db.rollback()
        return JSONResponse(
            status_code=400,
            content={"error": "Email or in-game name already taken"},
        )

    except Exception as e:
        logger.error(f"❌ Registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unexpected server error")

