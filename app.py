"""
app.py
Your Flask + SQLAlchemy backend for storing replay parse results.
"""

import os
import io
import time
import logging
import json
import pathlib
from datetime import datetime

from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text, Index

###############################################################################
# FLASK SETUP
###############################################################################
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Fix for deprecated postgres:// URLs
raw_db_url = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@aoe2-postgres:5432/aoe2"
)
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Optional: Enable SSL on Render
if "RENDER" in os.environ or "render.com" in raw_db_url:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "connect_args": {"sslmode": "require"}
    }

db = SQLAlchemy(app)

###############################################################################
# DATABASE MODEL
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

Index("ix_replay_iteration", GameStats.replay_file, GameStats.parse_iteration)
Index("ix_replay_hash_iteration", GameStats.replay_hash, GameStats.parse_iteration)

###############################################################################
# DB INIT
###############################################################################
with app.app_context():
    for attempt in range(10):
        try:
            db.session.execute(text("SELECT 1"))
            break
        except Exception:
            logging.warning(f"⏳ DB not ready (attempt {attempt+1}/10), retrying in 3s...")
            time.sleep(3)
    else:
        logging.error("❌ Database did not become ready in time.")
        exit(1)

    db.create_all()
    logging.info("✅ Tables created or verified existing.")

@app.route("/")
def index():
    return "API is live"

@app.route("/debug/game_count")
def debug_count():
    total = GameStats.query.count()
    finals = GameStats.query.filter_by(is_final=True).count()
    return jsonify({
        "total_games": total,
        "final_games": finals
    })


###############################################################################
# HELPER - parse replay from disk (optional legacy method)
###############################################################################
def parse_replay_full(replay_path):
    if not os.path.exists(replay_path):
        logging.error(f"❌ Replay not found: {replay_path}")
        return None

    try:
        from mgz import header, summary
        with open(replay_path, "rb") as f:
            file_bytes = f.read()

        h = header.parse(file_bytes)
        s = summary.Summary(io.BytesIO(file_bytes))

        stats = {
            "game_version": str(h.version),
            "map": {
                "name": s.get_map().get("name", "Unknown"),
                "size": s.get_map().get("size", "Unknown"),
            },
            "game_type": str(s.get_version()),
            "duration": int(s.get_duration() // 1000 if s.get_duration() > 48 * 3600 else s.get_duration()),
        }

        players = []
        winner = None
        for p in s.get_players():
            p_data = {
                "name": p.get("name", "Unknown"),
                "civilization": p.get("civilization", "Unknown"),
                "winner": p.get("winner", False),
                "score": p.get("score", 0),
            }
            players.append(p_data)
            if p_data["winner"]:
                winner = p_data["name"]

        stats["players"] = players
        stats["winner"] = winner or "Unknown"
        dt = extract_datetime_from_filename(os.path.basename(replay_path))
        stats["played_on"] = dt.isoformat() if dt else None

        logging.info(f"✅ parse_replay_full => {replay_path}")
        return stats

    except Exception as e:
        logging.error(f"❌ parse error: {e}")
        return None

def extract_datetime_from_filename(fname):
    import re
    match = re.search(r"@(\d{4})\.(\d{2})\.(\d{2}) (\d{6})", fname)
    if match:
        try:
            return datetime.strptime(f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}", "%Y-%m-%d %H%M%S")
        except ValueError:
            return None
    return None

###############################################################################
# API ROUTE: /api/parse_replay
###############################################################################
@app.route("/api/parse_replay", methods=["POST"])
def parse_new_replay():
    data = request.json
    replay_path = data.get("replay_file")
    replay_hash = data.get("replay_hash")
    parse_iteration = int(data.get("parse_iteration", 0))
    is_final = bool(data.get("is_final", False))  # <-- ✅

    logging.info(f"📝 Received replay: {replay_path} | Final: {is_final} | Iteration: {parse_iteration}")  # <-- ✅ Add this

    if not replay_path or not replay_hash:
        return jsonify({"error": "Missing replay_file or replay_hash."}), 400

    existing_final = GameStats.query.filter_by(replay_hash=replay_hash, is_final=True).first()
    if is_final and existing_final:
        logging.info(f"⏭️ Skipped: Final already stored for hash {replay_hash}")
        return jsonify({"message": "Replay already parsed as final. Skipped."}), 200

    new_game = GameStats(
        replay_file=replay_path,
        replay_hash=replay_hash,
        game_version=data.get("game_version"),
        map=json.dumps({
            "name": data.get("map_name", "Unknown"),
            "size": data.get("map_size", "Unknown")
        }),
        game_type=data.get("game_type"),
        duration=data.get("duration", 0),
        winner=data.get("winner", "Unknown"),
        players=json.dumps(data.get("players", [])),
        event_types="[]",
        key_events="[]",
        parse_iteration=parse_iteration,
        is_final=is_final,
        played_on=datetime.fromisoformat(data["played_on"]) if data.get("played_on") else None
    )

    try:
        db.session.add(new_game)
        db.session.commit()
    except Exception as e:
        logging.error(f"❌ DB commit failed: {e}")
        return jsonify({"error": "DB insert failed"}), 500

    return jsonify({"message": f"Replay stored (iteration {parse_iteration})"})

###############################################################################
# API ROUTE: /api/game_stats
###############################################################################
@app.route("/api/game_stats", methods=["GET"])
def game_stats():
    mode = request.args.get("mode", "final")

    if mode == "latest":
        # Get only latest parse_iteration per replay_hash
        subquery = db.session.query(
            GameStats.replay_hash,
            db.func.max(GameStats.parse_iteration).label("max_iter")
        ).group_by(GameStats.replay_hash).subquery()

        games = db.session.query(GameStats).join(
            subquery,
            (GameStats.replay_hash == subquery.c.replay_hash) &
            (GameStats.parse_iteration == subquery.c.max_iter)
        ).order_by(GameStats.played_on.desc().nullslast()).all()
    else:
        # Default mode: only is_final=True
        games = GameStats.query.filter_by(is_final=True).order_by(GameStats.played_on.desc().nullslast()).all()

    results = []
    for g in games:
        try:
            game_map = json.loads(g.map or "{}")
        except:
            game_map = {}
        try:
            players = json.loads(g.players or "[]")
        except:
            players = []
        try:
            event_types = json.loads(g.event_types or "[]")
        except:
            event_types = []
        try:
            key_events = json.loads(g.key_events or "[]")
        except:
            key_events = []

        results.append({
            "id": g.id,
            "replay_file": g.replay_file,
            "replay_hash": g.replay_hash,
            "parse_iteration": g.parse_iteration,
            "is_final": g.is_final,
            "game_version": g.game_version,
            "map": game_map,
            "game_type": g.game_type,
            "duration": g.duration,
            "winner": g.winner,
            "players": players,
            "event_types": event_types,
            "key_events": key_events,
            "timestamp": g.timestamp.isoformat(),
            "played_on": g.played_on.isoformat() if g.played_on else None
        })

    response = make_response(jsonify(results))
    response.headers["Cache-Control"] = "no-store"
    return response


###############################################################################
# RUN
###############################################################################
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host="0.0.0.0", port=8002)
