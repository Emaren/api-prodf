# routes/user_register.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from db.models import User
from db.db import get_db
from db.schemas import UserRegisterRequest

router = APIRouter()

@router.post("/api/user/register")
async def register_user(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        # ✅ Block duplicate UIDs (same user re-logging)
        existing_user = await db.execute(select(User).where(User.uid == payload.uid))
        user = existing_user.scalar_one_or_none()
        if user:
            return {"message": "User already exists"}

        # ✅ Block duplicate in-game names
        name_check = await db.execute(select(User).where(User.in_game_name == payload.in_game_name))
        name_conflict = name_check.scalar_one_or_none()
        if name_conflict:
            raise HTTPException(status_code=400, detail="In-game name already taken")

        # ✅ First user = admin
        count_result = await db.execute(select(func.count()).select_from(User))
        user_count = count_result.scalar()
        is_admin = user_count == 0

        new_user = User(
            uid=payload.uid,
            email=payload.email,
            in_game_name=payload.in_game_name,
            is_admin=is_admin,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {"message": "User registered", "is_admin": is_admin}

    except Exception as e:
        print(f"❌ Error during registration: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")
