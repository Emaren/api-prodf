# routes/user_exists.py

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_db
from db.models import User

router = APIRouter(tags=["user"])

@router.get("/exists")
async def user_exists_by_name(name: str, db_gen=Depends(get_db)):
    """
    GET /api/user/exists?name=...
    Checks if in-game name already exists.
    """
    async with db_gen as db:
        res = await db.execute(select(User).where(User.in_game_name == name))
        return {"exists": res.scalar_one_or_none() is not None}

@router.post("/exists")
async def user_exists_by_email(payload: dict, db_gen=Depends(get_db)):
    """
    POST /api/user/exists
    JSON payload: { "email": "..." }
    Checks if email is registered.
    """
    email = payload.get("email")
    if not email:
        return {"exists": False}
    async with db_gen as db:
        res = await db.execute(select(User).where(User.email == email))
        return {"exists": res.scalar_one_or_none() is not None}

@router.get("/get_email_from_ingame")
async def get_email_from_ingame(in_game_name: str, db_gen=Depends(get_db)):
    """
    GET /api/user/get_email_from_ingame?in_game_name=...
    Returns the email associated with an in-game name.
    """
    async with db_gen as db:
        result = await db.execute(select(User).where(User.in_game_name == in_game_name))
        user = result.scalar_one_or_none()
        return {"email": user.email if user else None}

@router.post("/get_email_from_ingame")
async def get_email_from_ingame_post(payload: dict, db_gen=Depends(get_db)):
    """
    POST /api/user/get_email_from_ingame
    JSON payload: { "in_game_name": "..." }
    Returns the email associated with an in-game name.
    """
    in_game_name = payload.get("in_game_name")
    if not in_game_name:
        return {"email": None}
    async with db_gen as db:
        result = await db.execute(select(User).where(User.in_game_name == in_game_name))
        user = result.scalar_one_or_none()
        return {"email": user.email if user else None}
