# routes/user_register.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from db.models import User
from db.db import get_db
from db.schemas import UserRegisterRequest
from pydantic import BaseModel


router = APIRouter()

class RegisterPayload(BaseModel):
    uid: str
    email: str
    in_game_name: str

@router.post("/api/user/register")
async def register_user(payload: UserRegisterRequest, db_gen=Depends(get_db)):
    async with db_gen as db:  # ✅ Use this pattern
        existing_user = await db.execute(
            select(User).where(User.uid == payload.uid)
        )
        user = existing_user.scalar_one_or_none()

        if user:
            return {"message": "User already exists"}

        # ✅ Count how many users exist to set first user as admin
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

        return {"message": "User registered", "is_admin": is_admin}
