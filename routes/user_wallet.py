from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.models.user import User
from db.db import get_db
from dependencies.auth import get_firebase_user

router = APIRouter(tags=["user"])

class WalletLinkRequest(BaseModel):
    wallet_address: str


@router.post("/link_wallet")
async def link_wallet(
    data: WalletLinkRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_firebase_user),
):
    uid = current_user["uid"]

    # Fetch user by UID
    result = await db.execute(select(User).where(User.uid == uid))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Optional: Prevent duplicate linking
    if user.wallet_address == data.wallet_address:
        return {"status": "already_linked", "wallet": user.wallet_address}

    user.wallet_address = data.wallet_address
    await db.commit()

    return {"status": "linked", "wallet": user.wallet_address}
