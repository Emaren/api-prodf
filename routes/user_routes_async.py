from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_db
from db.models import User, GameStats

router = APIRouter(prefix="/api/user", tags=["user"])


class UpdateNameRequest(BaseModel):
    uid: str
    in_game_name: str


class UpdateWalletRequest(BaseModel):
    uid: str
    wallet_address: str


@router.post("/update_name")
async def update_name(data: UpdateNameRequest, db_gen=Depends(get_db)):
    async with db_gen as db:
        result = await db.execute(select(User).where(User.uid == data.uid))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.in_game_name and user.lock_name:
            raise HTTPException(
                status_code=403, detail="Name change is locked during a match"
            )

        if user.in_game_name:
            match_query = await db.execute(
                select(GameStats).filter(
                    GameStats.is_final == False,
                    GameStats.players.cast(str).ilike(f"%{user.in_game_name}%"),
                )
            )
            active_match = match_query.scalar_one_or_none()
            if active_match:
                raise HTTPException(
                    status_code=403, detail="Cannot change name during an active match"
                )

        user.in_game_name = data.in_game_name
        await db.commit()
        return {"message": "Name updated", "verified": user.verified}


@router.post("/update_wallet")
async def update_wallet(data: UpdateWalletRequest, db_gen=Depends(get_db)):
    async with db_gen as db:
        result = await db.execute(select(User).where(User.uid == data.uid))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.wallet_address = data.wallet_address
        await db.commit()
        return {"message": "Wallet updated"}


@router.get("/online")
async def get_online_users(db_gen=Depends(get_db)):
    async with db_gen as db:
        result = await db.execute(select(User).where(User.in_game_name.isnot(None)))
        users = result.scalars().all()
        return [
            {
                "uid": u.uid,
                "in_game_name": u.in_game_name,
                "verified": u.verified,
            }
            for u in users
        ]


@router.post("/verify_token")
async def verify_token(authorization: str = "", db_gen=Depends(get_db)):
    async with db_gen as db:
        token = authorization.replace("Bearer ", "")
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
