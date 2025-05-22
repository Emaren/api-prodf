# routes/chain_id.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/api/chain-id")
async def get_chain_id():
    return JSONResponse(content={"chainId": "wolochain"})
