from db import db
from sqlalchemy import Index
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
    players = db.Column(db.Text)
    event_types = db.Column(db.Text)
    key_events = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    played_on = db.Column(db.DateTime, nullable=True)

    parse_iteration = db.Column(db.Integer, default=0)
    is_final = db.Column(db.Boolean, default=False)

# ✅ Add indexes for optimization
Index("ix_replay_iteration", GameStats.replay_file, GameStats.parse_iteration)
Index("ix_replay_hash_iteration", GameStats.replay_hash, GameStats.parse_iteration)
