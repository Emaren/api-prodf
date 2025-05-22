# routes/chain_id.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/chain-id")
async def get_chain_id():
    return {"chainId": "wolochain"}
