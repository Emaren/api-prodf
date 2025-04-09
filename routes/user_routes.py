import os
from flask import Blueprint, request, jsonify
from db import db
from models import User, GameStats
from sqlalchemy import cast, Text

# All user endpoints => /api/user/...
user_bp = Blueprint("user", __name__, url_prefix="/api/user")

@user_bp.route("/register", methods=["POST"])
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

    new_user = User(
        uid=uid,
        email=email,
        in_game_name=in_game_name,
        verified=False
    )
    db.session.add(new_user)
    db.session.commit()
    db.session.refresh(new_user)

    return jsonify({
        "message": "User registered",
        "user": {
            "uid": new_user.uid,
            "email": new_user.email,
            "in_game_name": new_user.in_game_name,
            "verified": new_user.verified
        }
    })


@user_bp.route("/me", methods=["POST", "GET"])
def get_user_by_uid():
    if request.method == "GET":
        # Just a test GET path?
        return jsonify({
            "uid": "dev",
            "email": "dev@local",
            "in_game_name": "dev_player",
            "verified": True,
            "wallet_address": "DEVWALLET123",
            "lock_name": None
        })

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


@user_bp.route("/update_name", methods=["POST"])
def update_player_name():
    data = request.get_json()
    uid = data.get("uid")
    new_name = data.get("in_game_name")

    if not uid or not new_name:
        return jsonify({"error": "Missing uid or in_game_name"}), 400

    user = db.session.query(User).filter_by(uid=uid).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # If user has an existing name, check if we can change it
    if user.in_game_name:
        if user.lock_name:
            return jsonify({"error": "Name change is locked during a match."}), 403

        # IMPORTANT FIX: cast the players JSON column to text for ILIKE to work
        active_match = db.session.query(GameStats).filter(
            GameStats.is_final == False,
            cast(GameStats.players, Text).ilike(f"%{user.in_game_name}%")
        ).first()

        if active_match:
            return jsonify({"error": "Cannot change name during an active match."}), 403

    user.in_game_name = new_name
    db.session.commit()
    return jsonify({"message": "Name updated", "verified": user.verified})


@user_bp.route("/update_wallet", methods=["POST"])
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


@user_bp.route("/online", methods=["GET"])
def get_online_users():
    # Only users with non-null in_game_name
    users = db.session.query(User).filter(User.in_game_name.isnot(None)).all()
    return jsonify([
        {
            "uid": u.uid,
            "in_game_name": u.in_game_name,
            "verified": u.verified
        }
        for u in users
    ])


@user_bp.route("/verify_token", methods=["POST"])
def get_current_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user = User.query.filter_by(token=token).first()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'id': user.id,
        'uid': user.uid,
        'email': user.email,
        'in_game_name': user.in_game_name,
        'verified': user.verified
    })
