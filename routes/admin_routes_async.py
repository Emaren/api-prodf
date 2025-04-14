from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User
from db.db import get_db
import os

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def verify_admin_token(authorization: str = Header(...)):
    expected = f"Bearer {os.getenv('ADMIN_TOKEN', 'secretadmin')}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/users")
async def list_users(authorization: str = Header(...), db_gen=Depends(get_db)):
    async with db_gen as db:
        verify_admin_token(authorization)

        result = await db.execute(select(User))
        users = result.scalars().all()

        return [
            {
                "uid": u.uid,
                "email": u.email,
                "in_game_name": u.in_game_name,
                "verified": u.verified,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
