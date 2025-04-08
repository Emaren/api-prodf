from db import db
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime

###############################################################################
# DATABASE MODEL: User
###############################################################################
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String, unique=True, nullable=False)         # Firebase/Supabase UID
    email = db.Column(db.String)
    in_game_name = db.Column(db.String, nullable=True)
    verified = db.Column(db.Boolean, default=False)
    wallet_address = db.Column(db.String(100), nullable=True)       # ✅ NEW
    lock_name = db.Column(db.Boolean, default=False)                # ✅ NEW
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(128), nullable=True)

    def __repr__(self):
        return f"<User {self.uid}>"

###############################################################################
# DATABASE MODEL: GameStats
###############################################################################
class GameStats(db.Model):
    __tablename__ = "game_stats"

    id = db.Column(db.Integer, primary_key=True)
    replay_file = db.Column(db.String(500), nullable=False)
    replay_hash = db.Column(db.String(64), nullable=False)

    game_version = db.Column(db.String(50))
    map = db.Column(db.String(100))
    game_type = db.Column(db.String(50))
    duration = db.Column(db.Integer)
    winner = db.Column(db.String(100))
    players = db.Column(JSON)
    event_types = db.Column(JSON)
    key_events = db.Column(JSON)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    played_on = db.Column(db.DateTime, nullable=True)

    parse_iteration = db.Column(db.Integer, default=0)
    is_final = db.Column(db.Boolean, default=False)

    __table_args__ = (
        Index("ix_replay_iteration", "replay_file", "parse_iteration"),
        Index("ix_replay_hash_iteration", "replay_hash", "parse_iteration"),
        UniqueConstraint("replay_hash", "is_final", name="uq_replay_final"),
    )

    def __repr__(self):
        return f"<GameStats {self.replay_hash} - Final: {self.is_final}>"
