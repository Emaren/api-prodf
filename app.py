# app.py
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
import logging
import os

from db.db import init_db_async, get_db
from db.models import GameStats, User
from firebase_utils import initialize_firebase
from firebase_utils import get_user_from_token

# ✅ Routes
from routes import (
    user_me,
    user_register,
    user_exists,
    replay_routes_async,
    debug_routes_async,
    admin_routes_async,
    bets,
    user_ping,
    chain_id,
    traffic_route,
    user_wallet,
)

print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")

class LogRequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"📩 Incoming Request: {request.method} {request.url}")
        if "authorization" in request.headers:
            token_preview = request.headers["authorization"][:40]
            print(f"🔑 Auth Header (first 40 chars): {token_preview}...")
        else:
            print("⚠️ No Authorization header present.")
        return await call_next(request)

app = FastAPI()
app.add_middleware(LogRequestMiddleware)

# ✅ Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    initialize_firebase()
    await init_db_async()
    for route in app.routes:
        if "/user" in route.path:
            print(f"🔍 {route.methods} → {route.path} [{route.name}]")

# ✅ Register routers
app.include_router(user_register.router, prefix="/api/user")
app.include_router(user_me.router,       prefix="/api/user")
app.include_router(user_exists.router,   prefix="/api/user")
app.include_router(user_ping.router,     prefix="/api/user")
app.include_router(user_wallet.router,   prefix="/api/user")
app.include_router(replay_routes_async.router)
app.include_router(debug_routes_async.router)
app.include_router(admin_routes_async.router)
app.include_router(bets.router)
app.include_router(chain_id.router)
app.include_router(traffic_route.router)

@app.get("/")
def root():
    return {"message": "AoE2 Betting Backend is running!"}

@app.get("/api/game_stats")
async def get_game_stats(db_gen=Depends(get_db)):
    try:
        async with db_gen as db:
            result = await db.execute(
                select(GameStats)
                .where(GameStats.is_final == True)
                .order_by(GameStats.timestamp.desc())
            )
            games = result.scalars().all()
            unique_games = {}
            for game in games:
                if game.replay_hash not in unique_games:
                    unique_games[game.replay_hash] = game

            logging.getLogger(__name__).info(f"📊 Returning {len(unique_games)} unique games from DB")
            return [g.to_dict() for g in unique_games.values()]
    except Exception as e:
        logging.error(f"❌ Failed to fetch game stats: {e}", exc_info=True)
        return []

# ✅ NEW: Link Wallet Route
@app.post("/api/user/link_wallet")
async def link_wallet(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        data = await request.json()
        address = data.get("address")
        if not address:
            raise HTTPException(status_code=400, detail="Missing wallet address")

        # 🔐 Authenticate Firebase Token
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        token = auth_header.split("Bearer ")[1]
        user_info = get_user_from_token(token)
        if not user_info or "uid" not in user_info:
            raise HTTPException(status_code=401, detail="Invalid Firebase token")

        firebase_uid = user_info["uid"]

        # 🔄 Update DB
        result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        await db.execute(
            update(User)
            .where(User.id == user.id)
            .values(wallet_address=address)
        )
        await db.commit()
        return {"message": "Wallet linked successfully"}
    except Exception as e:
        logging.error(f"❌ Failed to link wallet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
