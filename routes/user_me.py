from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_db
from db.models import User

router = APIRouter()


class UserMeRequest(BaseModel):
    uid: str | None = None
    email: str | None = None


@router.post("/api/user/me")
async def get_user_me(data: UserMeRequest, db_gen=Depends(get_db)):
    async with db_gen as db:
        user = None

        if data.uid:
            result = await db.execute(select(User).where(User.uid == data.uid))
            user = result.scalar_one_or_none()

        if not user and data.email:
            result = await db.execute(select(User).where(User.email == data.email))
            user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user.to_dict()
