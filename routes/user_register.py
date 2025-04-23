from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.db import get_db
from db.models import User
from datetime import datetime

router = APIRouter(prefix="/api/user", tags=["user"])

class RegisterUserRequest(BaseModel):
    uid: str
    email: str
    in_game_name: str

@router.post("/register")
async def register_user(data: RegisterUserRequest, db_gen=Depends(get_db)):
    async with db_gen as db:
        # Check if UID already exists
        result = await db.execute(select(User).where(User.uid == data.uid))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")

        # Create new user
        new_user = User(
            uid=data.uid,
            email=data.email,
            in_game_name=data.in_game_name,
            verified=False,
            created_at=datetime.utcnow(),
        )
        db.add(new_user)
        await db.commit()

        return {"message": "User registered successfully"}
