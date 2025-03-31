###############################################################################
# app.py
###############################################################################
import os
import io
import time
import logging
import json
import pathlib
from datetime import datetime

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text
from mgz import header, summary

###############################################################################
# FLASK SETUP
###############################################################################
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 20,
    "max_overflow": 40,
    "pool_timeout": 30,
    "pool_recycle": 1800,
}
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://aoe2user:secretpassword@aoe2-postgres:5432/aoe2db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

###############################################################################
# DATABASE MODEL
###############################################################################
class GameStats(db.Model):
    __tablename__ = "game_stats"

    id = db.Column(db.Integer, primary_key=True)
    replay_file = db.Column(db.String(500), unique=True, nullable=False)
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

###############################################################################
# HELPER: Infer Resign Winner (Disabled for now)
###############################################################################
def infer_resign_winner(file_bytes, players):
    return None  # TODO: Properly parse resign actions using mgz.fast

###############################################################################
# PARSE LOGIC
###############################################################################
def parse_replay_full(replay_path):
    if not os.path.exists(replay_path):
        logging.error(f"❌ Not found: {replay_path}")
        return None

    try:
        with open(replay_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        logging.error(f"❌ Reading error: {e}")
        return None

    stats = {}
    try:
        h = header.parse(file_bytes)
        stats["game_version"] = str(h.version)
    except Exception as e:
        logging.error(f"❌ parse header error: {e}")
        return None

    try:
        s = summary.Summary(io.BytesIO(file_bytes))
        raw_map = s.get_map()
        stats["map"] = {
            "name": raw_map.get("name", "Unknown"),
            "size": raw_map.get("size", "Unknown"),
        }
        stats["game_type"] = str(s.get_version())

        raw_duration = s.get_duration()
        if raw_duration > (20 * 3600):
            raw_duration //= 1000
        stats["duration"] = int(raw_duration)

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

        if not winner and len(players) == 2:
            r_index = infer_resign_winner(file_bytes, players)
            if r_index is not None:
                players[r_index]["winner"] = True
                players[1 - r_index]["winner"] = False
                winner = players[r_index]["name"]
                logging.info(f"🏆 Winner determined by Resign: {winner}")

        stats["winner"] = winner if winner else "Unknown"
        stats["players"] = players

    except Exception as e:
        logging.error(f"❌ summary error: {e}")
        return None

    stats["replay_file"] = replay_path
    dt = extract_datetime_from_filename(os.path.basename(replay_path))
    stats["played_on"] = dt.isoformat() if dt else None

    logging.info(f"✅ Parsed replay: {stats['replay_file']}")
    logging.info(f"🕓 Played on: {stats['played_on']}")
    logging.info(f"🎯 Winner: {stats['winner']}")

    return stats

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
# API ROUTES
###############################################################################
@app.route("/api/parse_replay", methods=["POST"])
def parse_new_replay():
    data = request.json
    replay_path = data.get("replay_file")
    if not replay_path:
        return jsonify({"error": "No replay_file provided."}), 400

    replay_path = str(pathlib.Path(replay_path).expanduser().resolve())

    existing = GameStats.query.filter_by(replay_file=replay_path).first()
    if existing:
        logging.info(f"♻️ Replay already exists. Replacing: {replay_path}")
        db.session.delete(existing)
        db.session.commit()

    if not os.path.exists(replay_path):
        return jsonify({"error": f"File not found: {replay_path}"}), 400

    parsed = parse_replay_full(replay_path)
    if not parsed:
        return jsonify({"error": "Failed to parse replay"}), 500

    new_game = GameStats(
        replay_file=replay_path,
        game_version=parsed.get("game_version"),
        map=json.dumps(parsed.get("map", {})),
        game_type=parsed.get("game_type"),
        duration=parsed.get("duration", 0),
        winner=parsed.get("winner", "Unknown"),
        players=json.dumps(parsed.get("players", [])),
        event_types="[]",
        key_events="[]",
        played_on=datetime.fromisoformat(parsed["played_on"]) if parsed.get("played_on") else None
    )

    db.session.add(new_game)
    try:
        db.session.commit()
    except Exception as e:
        logging.error(f"❌ DB commit failed: {e}")
        return jsonify({"error": "DB insert failed"}), 500

    return jsonify({"message": "Replay parsed and stored successfully!"})

@app.route("/api/game_stats", methods=["GET"])
def game_stats():
    all_games = GameStats.query.order_by(
        GameStats.played_on.desc().nullslast(),
        GameStats.timestamp.desc()
    ).all()

    results = []
    for g in all_games:
        try:
            game_map = json.loads(g.map) if g.map else {}
        except Exception:
            game_map = {}

        try:
            game_players = json.loads(g.players) if g.players else []
        except Exception:
            game_players = []

        try:
            event_types = json.loads(g.event_types) if g.event_types else []
        except Exception:
            event_types = []

        try:
            key_events = json.loads(g.key_events) if g.key_events else []
        except Exception:
            key_events = []

        results.append({
            "id": g.id,
            "replay_file": g.replay_file,
            "game_version": str(g.game_version),
            "map": game_map,
            "game_type": g.game_type,
            "duration": g.duration,
            "winner": g.winner,
            "players": game_players,
            "event_types": event_types,
            "key_events": key_events,
            "timestamp": g.timestamp.isoformat(),
            "played_on": g.played_on.isoformat() if g.played_on else None
        })


    return jsonify(results)

###############################################################################
# MAIN
###############################################################################
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    app.run(debug=True, host="0.0.0.0", port=8002)
