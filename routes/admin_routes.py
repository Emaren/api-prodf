import os
from flask import Blueprint, request, jsonify, abort
from db import db
from models import User

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/users", methods=["GET"])
def list_users():
    # Verify admin token
    token = request.headers.get("Authorization")
    if token != f"Bearer {os.getenv('ADMIN_TOKEN', 'secretadmin')}":
        abort(401, description="Unauthorized")

    try:
        users = User.query.all()
        return jsonify([
            {
                "uid": u.uid,
                "email": u.email,
                "in_game_name": u.in_game_name,
                "verified": u.verified,
                "created_at": (
                    u.created_at.isoformat()
                    if hasattr(u, "created_at") and u.created_at
                    else None
                )
            }
            for u in users
        ])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Internal error: {str(e)}"}), 500
