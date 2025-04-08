from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
import json
import os
from werkzeug.utils import secure_filename

from models import GameStats, User
from db import db
from utils.replay_parser import parse_replay_full, hash_replay_file

# This blueprint doesn't have a prefix, so routes are absolute
replay_bp = Blueprint("replay", __name__)

@replay_bp.route("/")
def index():
    return "API is live"

@replay_bp.route("/api/parse_replay", methods=["POST"])
def parse_new_replay():
    data = request.json
    replay_path = data.get("replay_file")
    replay_hash = data.get("replay_hash")
    parse_iteration = int(data.get("parse_iteration", 0))
    is_final = bool(data.get("is_final", False))

    if not replay_path or not replay_hash:
        return jsonify({"error": "Missing replay_file or replay_hash."}), 400

    if is_final:
        existing_final = GameStats.query.filter_by(replay_hash=replay_hash, is_final=True).first()
        if existing_final:
            return jsonify({"message": "Replay already parsed as final. Skipped."}), 200

    # Store parsed data
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

        # ✅ Verification logic: match users by normalized in-game names
        player_names = [p.get("name", "").strip().lower() for p in data.get("players", [])]
        matched_users = db.session.query(User).filter(
            db.func.lower(User.in_game_name).in_(player_names)
        ).all()

        for user in matched_users:
            if not user.verified:
                user.verified = True
                print(f"✅ Verified user: {user.uid} ({user.in_game_name})")
            user.lock_name = not is_final
        db.session.commit()

    except Exception as e:
        print(f"❌ DB insert or verification failed: {e}")
        return jsonify({"error": "DB insert failed"}), 500

    return jsonify({"message": f"Replay stored (iteration {parse_iteration})"})

@replay_bp.route("/api/game_stats", methods=["GET"])
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

@replay_bp.route("/api/upload_replay", methods=["POST"])
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
        return jsonify({"error": "DB insert failed"}), 500

    return jsonify({"message": "Replay uploaded and stored."})
