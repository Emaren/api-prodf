"""
app.py — Flask + SQLAlchemy backend for storing replay parse results.
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask, jsonify, request, make_response, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename

from models import GameStats, User
from db import db, init_db
from utils.replay_parser import parse_replay_full, hash_replay_file

# ─────────────────────────────────────────────────────────────────────────────
# FLASK SETUP
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database config
raw_db_url = os.getenv("DATABASE_URL")
if not raw_db_url:
    user = os.getenv("PGUSER", "postgres")
    pw = os.getenv("PGPASSWORD", "postgres")
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    dbname = os.getenv("PGDATABASE", "aoe2")
    raw_db_url = f"postgresql://{user}:{pw}@{host}:{port}/{dbname}"
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = raw_db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
if "RENDER" in os.environ or "render.com" in raw_db_url:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"connect_args": {"sslmode": "require"}}

init_db(app)

# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return "API is live"

@app.route("/debug/game_count")
def debug_count():
    return jsonify({
        "total_games": GameStats.query.count(),
        "final_games": GameStats.query.filter_by(is_final=True).count()
    })

@app.route("/api/parse_replay", methods=["POST"])
def parse_new_replay():
    data = request.json
    replay_path = data.get("replay_file")
    replay_hash = data.get("replay_hash")
    parse_iteration = int(data.get("parse_iteration", 0))
    is_final = bool(data.get("is_final", False))

    logging.info(f"📝 Received replay: {replay_path} | Final: {is_final} | Iteration: {parse_iteration}")

    if not replay_path or not replay_hash:
        return jsonify({"error": "Missing replay_file or replay_hash."}), 400

    if is_final:
        existing_final = GameStats.query.filter_by(replay_hash=replay_hash, is_final=True).first()
        if existing_final:
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

        player_names = [p.get("name") for p in data.get("players", [])]
        matched_users = db.session.query(User).filter(User.in_game_name.in_(player_names)).all()
        for user in matched_users:
            if not user.verified:
                user.verified = True
                logging.info(f"✅ Verified user: {user.uid} ({user.in_game_name})")
            user.lock_name = not is_final
        db.session.commit()

    except Exception as e:
        logging.error(f"❌ DB commit failed: {e}")
        return jsonify({"error": "DB insert failed"}), 500

    return jsonify({"message": f"Replay stored (iteration {parse_iteration})"})

@app.route("/api/game_stats", methods=["GET"])
def game_stats():
    mode = request.args.get("mode", "final")

    if mode == "latest":
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
        games = GameStats.query.filter_by(is_final=True).order_by(GameStats.played_on.desc().nullslast()).all()

    results = []
    for g in games:
        results.append({
            "id": g.id,
            "replay_file": g.replay_file,
            "replay_hash": g.replay_hash,
            "parse_iteration": g.parse_iteration,
            "is_final": g.is_final,
            "game_version": g.game_version,
            "map": json.loads(g.map or "{}"),
            "game_type": g.game_type,
            "duration": g.duration,
            "winner": g.winner,
            "players": json.loads(g.players or "[]"),
            "event_types": json.loads(g.event_types or "[]"),
            "key_events": json.loads(g.key_events or "[]"),
            "timestamp": g.timestamp.isoformat(),
            "played_on": g.played_on.isoformat() if g.played_on else None
        })

    response = make_response(jsonify(results))
    response.headers["Cache-Control"] = "no-store"
    return response

@app.route("/api/upload_replay", methods=["POST"])
def upload_replay():
    if 'file' not in request.files:
        return jsonify({"error": "Missing file in form data"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No filename provided"}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join("/tmp", filename)
    file.save(temp_path)

    parsed = parse_replay_full(temp_path)
    if not parsed:
        return jsonify({"error": "Failed to parse replay"}), 500

    parsed["replay_file"] = temp_path
    parsed["replay_hash"] = hash_replay_file(temp_path)
    parsed["parse_iteration"] = 1
    parsed["is_final"] = True

    try:
        new_game = GameStats(
            replay_file=parsed["replay_file"],
            replay_hash=parsed["replay_hash"],
            game_version=parsed.get("game_version"),
            map=json.dumps(parsed.get("map", {})),
            game_type=parsed.get("game_type"),
            duration=parsed.get("duration", 0),
            winner=parsed.get("winner", "Unknown"),
            players=json.dumps(parsed.get("players", [])),
            event_types="[]",
            key_events="[]",
            parse_iteration=parsed["parse_iteration"],
            is_final=parsed["is_final"],
            played_on=datetime.fromisoformat(parsed["played_on"]) if parsed.get("played_on") else None
        )
        db.session.add(new_game)
        db.session.commit()
    except Exception as e:
        logging.error(f"❌ Upload DB commit failed: {e}")
        return jsonify({"error": "DB insert failed"}), 500

    return jsonify({"message": "Replay uploaded and stored."}), 200

@app.route("/debug/delete_all", methods=["DELETE"])
def delete_all():
    if os.getenv("ENABLE_DEV_ENDPOINTS") != "true":
        return jsonify({"error": "Debug endpoint disabled"}), 403
    db.session.query(GameStats).delete()
    db.session.query(User).delete()
    db.session.commit()
    return jsonify({"message": "All game stats and users deleted."})

@app.route("/api/register_user", methods=["POST"])
def register_user():
    data = request.get_json()
    uid = data.get("uid")
    email = data.get("email")
    in_game_name = data.get("in_game_name")

    if not uid:
        return jsonify({"error": "Missing uid"}), 400

    existing = db.session.query(User).filter_by(uid=uid).first()
    if existing:
        return jsonify({"message": "User already exists"}), 200

    new_user = User(uid=uid, email=email, in_game_name=in_game_name, verified=False)
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)

    return jsonify({"message": "User registered", "user": {
        "uid": new_user.uid,
        "email": new_user.email,
        "in_game_name": new_user.in_game_name,
        "verified": new_user.verified
    }})

@app.route("/api/user/me", methods=["POST"])
def get_user_by_uid():
    data = request.get_json()
    uid = data.get("uid")
    if not uid:
        return jsonify({"error": "Missing uid"}), 400

    user = db.session.query(User).filter_by(uid=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "uid": user.uid,
        "email": user.email,
        "in_game_name": user.in_game_name,
        "verified": user.verified,
        "wallet_address": user.wallet_address,
        "lock_name": user.lock_name
    })

@app.route("/api/user/update_name", methods=["POST"])
def update_player_name():
    data = request.get_json()
    uid = data.get("uid")
    new_name = data.get("in_game_name")

    if not uid or not new_name:
        return jsonify({"error": "Missing uid or name"}), 400

    user = db.session.query(User).filter_by(uid=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    if user.lock_name:
        return jsonify({"error": "Name change is locked during a match."}), 403

    active_match = db.session.query(GameStats).filter(
        GameStats.is_final == False,
        GameStats.players.ilike(f"%{user.in_game_name}%")
    ).first()

    if active_match:
        return jsonify({"error": "Cannot change name during an active match."}), 403

    user.in_game_name = new_name
    db.session.commit()
    return jsonify({"message": "Name updated", "verified": user.verified})

@app.route("/api/user/update_wallet", methods=["POST"])
def update_wallet():
    data = request.get_json()
    uid = data.get("uid")
    wallet = data.get("wallet_address")

    if not uid or not wallet:
        return jsonify({"error": "Missing uid or wallet_address"}), 400

    user = db.session.query(User).filter_by(uid=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.wallet_address = wallet
    db.session.commit()
    return jsonify({"message": "Wallet address updated"})

@app.route("/admin/users", methods=["GET"])
def list_users():
    token = request.headers.get("Authorization")
    if token != f"Bearer {os.getenv('ADMIN_TOKEN', 'secretadmin')}":
        abort(401, description="Unauthorized")

    users = User.query.all()
    return jsonify([
        {
            "uid": u.uid,
            "email": u.email,
            "in_game_name": u.in_game_name,
            "verified": u.verified,
            "created_at": u.created_at.isoformat()
        } for u in users
    ])

@app.route("/api/online_users")
def get_online_users():
    users = db.session.query(User).filter(User.in_game_name.isnot(None)).all()
    return jsonify([
        {
            "uid": u.uid,
            "in_game_name": u.in_game_name,
            "verified": u.verified
        } for u in users
    ])

# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, host="0.0.0.0", port=8002)
