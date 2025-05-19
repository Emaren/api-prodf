from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime,
    UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSON
from db.db import async_session
from sqlalchemy.orm import declarative_base

Base = declarative_base()

import os
import json
from pprint import pformat
from logging import getLogger

# ───────────────────────────────────────────────
# 🌐 Environment Check
# ───────────────────────────────────────────────
def is_render():
    return os.getenv("RENDER") == "1"

# ───────────────────────────────────────────────
# 🧍 User Model
# ───────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    uid = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, index=True)
    in_game_name = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    wallet_address = Column(String(100), nullable=True)
    lock_name = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    token = Column(String(128), nullable=True)
    last_seen = Column(DateTime, default=None)  # ✅ NEW: for online tracking

    def __repr__(self):
        return f"<User {self.uid}>"

    def to_dict(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "email": self.email,
            "in_game_name": self.in_game_name,
            "verified": self.verified,
            "wallet_address": self.wallet_address,
            "lock_name": self.lock_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "token": self.token,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,  # ✅ Include in output
        }

# ───────────────────────────────────────────────
# 🧾 GameStats Model
# ───────────────────────────────────────────────
class GameStats(Base):
    __tablename__ = "game_stats"

    id = Column(Integer, primary_key=True)
    replay_file = Column(String(500), nullable=False)
    replay_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    game_version = Column(String(50))
    map = Column(String(100))
    game_type = Column(String(50))
    duration = Column(Integer)
    game_duration = Column(Integer)
    winner = Column(String(100))
    players = Column(JSON)
    event_types = Column(JSON)
    key_events = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    played_on = Column(DateTime, nullable=True)

    parse_iteration = Column(Integer, default=0)
    is_final = Column(Boolean, default=False)

    disconnect_detected = Column(Boolean, default=False)
    parse_source = Column(String(20), default="unknown")
    parse_reason = Column(String(50), default="unspecified")
    original_filename = Column(String(255), nullable=True)

    __table_args__ = (
        Index("ix_replay_iteration", "replay_file", "parse_iteration"),
        Index("ix_replay_hash_iteration", "replay_hash", "parse_iteration"),
        UniqueConstraint("replay_hash", "is_final", name="uq_replay_final"),
    )

    def __repr__(self):
        return f"<GameStats {self.replay_hash} - Final: {self.is_final}>"

    def to_dict(self):
        logger = getLogger(__name__)
        trace_enabled = os.getenv("ENABLE_TRACE_LOGS", "true").lower() == "true"

        try:
            map_data = json.loads(self.map) if isinstance(self.map, str) else self.map
        except Exception:
            map_data = {"name": "Unknown", "size": "Unknown"}

        try:
            players = json.loads(self.players) if isinstance(self.players, str) else self.players
        except Exception:
            players = []

        resigns = len([e for e in (self.event_types or []) if e == "resign"])
        anomalies = any(k for k in (self.key_events or {}) if "anomaly" in k.lower())

        trace_block = (
            "\n📊 Final Game Parsed\n"
            f"📁 File: {self.replay_file}\n"
            f"📎 Original: {self.original_filename or 'N/A'}\n"
            f"🏷️  Hash: {self.replay_hash}\n"
            f"⚙️  Source: {self.parse_source or 'unknown'}\n"
            f"🧪 Reason: {self.parse_reason or 'unspecified'}\n"
            f"⏱️  Duration: {self.duration} sec\n"
            f"🗺️  Map: {map_data.get('name', 'Unknown')} ({map_data.get('size', 'Unknown')})\n"
            f"🏆 Winner: {self.winner or 'Unknown'}\n"
            f"🧩 Iteration: {self.parse_iteration}\n"
            f"🚪 Resigns: {resigns}\n"
            f"🚨 Anomalies: {'Yes' if anomalies else 'No'}\n"
            f"❌ Disconnect: {'Yes' if self.disconnect_detected else 'No'}\n"
            f"👥 Players:\n{pformat(players)}"
        )

        if trace_enabled and not is_render():
            logger.debug(trace_block)
            try:
                trace_path = self.replay_file + ".trace"
                with open(trace_path, "w") as f:
                    f.write(trace_block + "\n")
                with open("trace.index", "a") as idx:
                    idx.write(f"{datetime.utcnow().isoformat()} - {self.replay_file}\n")
            except Exception as e:
                logger.warning(f"❌ Failed to write trace files: {e}")

        return {
            "id": self.id,
            "replay_file": self.replay_file,
            "replay_hash": self.replay_hash,
            "game_version": self.game_version,
            "map": map_data,
            "game_type": self.game_type,
            "duration": self.duration,
            "game_duration": self.game_duration,
            "winner": self.winner,
            "players": players,
            "event_types": self.event_types,
            "key_events": self.key_events,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "played_on": self.played_on.isoformat() if self.played_on else None,
            "parse_iteration": self.parse_iteration,
            "is_final": self.is_final,
            "disconnect_detected": self.disconnect_detected,
            "parse_source": self.parse_source,
            "parse_reason": self.parse_reason,
            "original_filename": self.original_filename,
        }
