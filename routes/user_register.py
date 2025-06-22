# routes/user_register.py (🔥 fully patched production version)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from db.models import User
from db.db import get_db
from db.schemas import UserRegisterRequest
from dependencies.auth import get_firebase_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/api/user/register")
async def register_user(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
    firebase_user=Depends(get_firebase_user)
):
    try:
        uid = firebase_user["uid"]
        email = firebase_user.get("email")

        # Handle frontend bugs sending empty names
        if not payload.in_game_name or not payload.in_game_name.strip():
            raise HTTPException(
                status_code=400,
                detail={"field": "in_game_name", "error": "In-game name cannot be blank"}
            )

        # ✅ Check if UID exists in Postgres
        result = await db.execute(select(User).where(User.uid == uid))
        user = result.scalar_one_or_none()

        if user:
            logger.info(f"✅ User {uid} already exists")
            return {"message": "User already exists"}

        # ✅ Check for duplicate in-game name
        name_result = await db.execute(select(User).where(User.in_game_name == payload.in_game_name))
        name_conflict = name_result.scalar_one_or_none()
        if name_conflict:
            raise HTTPException(
                status_code=400,
                detail={"field": "in_game_name", "error": "In-game name already taken"}
            )

        # ✅ Handle first-user auto-admin logic
        count_result = await db.execute(select(func.count()).select_from(User))
        total_users = count_result.scalar()
        is_admin = total_users == 0

        new_user = User(
            uid=uid,
            email=email,
            in_game_name=payload.in_game_name,
            verified=False,
            created_at=datetime.utcnow(),
            is_admin=is_admin
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"✅ Registered: {uid} ({email})")
        return {"message": "User registered", "is_admin": is_admin}

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="In-game name already taken")

    except Exception as e:
        logger.error(f"❌ Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")
