from flask import Blueprint, jsonify, request
import os
from db import db
from models import GameStats, User

debug_bp = Blueprint("debug", __name__, url_prefix="/debug")

@debug_bp.route("/game_count", methods=["GET"])
def debug_count():
    return jsonify({
        "total_games": GameStats.query.count(),
        "final_games": GameStats.query.filter_by(is_final=True).count()
    })

@debug_bp.route("/delete_all", methods=["DELETE"])
def delete_all():
    if os.getenv("ENABLE_DEV_ENDPOINTS") != "true":
        return jsonify({"error": "Debug endpoint disabled"}), 403

    db.session.query(GameStats).delete()
    db.session.query(User).delete()
    db.session.commit()
    return jsonify({"message": "All game stats and users deleted."})
