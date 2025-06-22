# sync_firebase_users.py (final version)
import os
import asyncio
from datetime import datetime

import firebase_admin
from firebase_admin import auth, credentials

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from db.models import User

# 🔑 Load Firebase service account key
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# 🔌 Postgres connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aoe2user:secretpassword@localhost:5432/aoe2db"
)
engine = create_async_engine(DATABASE_URL)
Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# 🔁 Sync users (paged full sync)
async def sync_users():
    async with Session() as session:
        count = 0
        page = auth.list_users()

        while True:
            for user in page.users:
                uid = user.uid
                email = user.email

                # Ensure fallback placeholder name for empty display names
                raw_name = user.display_name.strip() if user.display_name else f"firebase_{uid[:6]}"

                print(f"🔍 Checking {uid} - {email} - {raw_name}")

                result = await session.execute(
                    User.__table__.select().where(User.uid == uid)
                )
                existing = result.scalar_one_or_none()

                if existing:
                    print(f"✅ Already exists: {uid}")
                else:
                    print(f"➕ Adding: {uid}")
                    session.add(User(
                        uid=uid,
                        email=email,
                        in_game_name=raw_name,
                        verified=False,
                        created_at=datetime.utcnow()
                    ))
                    count += 1

            if page.has_next_page:
                page = page.get_next_page()
            else:
                break

        await session.commit()
        print(f"✅ Sync complete. {count} new users added.")

# 🚀 Run it
if __name__ == "__main__":
    asyncio.run(sync_users())
