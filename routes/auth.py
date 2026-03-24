from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Player, PlayerStats
from utils.jwt_helper import create_token, require_auth
from datetime import datetime
import uuid

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password") or not data.get("display_name"):
        return jsonify({"error": "Missing required fields"}), 400
    if Player.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already taken"}), 409
    player = Player(
        id=str(uuid.uuid4()),
        username=data["username"].lower().strip(),
        password_hash=generate_password_hash(data["password"]),
        display_name=data["display_name"].strip()
    )
    stats = PlayerStats(player_id=player.id)
    db.session.add(player)
    db.session.add(stats)
    db.session.commit()
    token = create_token(player.id)
    return jsonify({
        "token": token,
        "player_id": player.id,
        "display_name": player.display_name
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Missing credentials"}), 400
    player = Player.query.filter_by(username=data["username"].lower().strip()).first()
    if not player or not check_password_hash(player.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    if player.is_banned:
        if player.ban_expires and player.ban_expires < datetime.utcnow():
            player.is_banned = False
            db.session.commit()
        else:
            return jsonify({
                "error": "Account banned",
                "reason": player.ban_reason,
                "expires": player.ban_expires.isoformat() if player.ban_expires else "permanent"
            }), 403
    player.last_seen = datetime.utcnow()
    db.session.commit()
    token = create_token(player.id)
    return jsonify({
        "token": token,
        "player_id": player.id,
        "display_name": player.display_name,
        "is_muted": player.is_muted
    }), 200

@auth_bp.route("/validate", methods=["GET"])
@require_auth
def validate(current_player):
    return jsonify({
        "valid": True,
        "player_id": current_player.id,
        "display_name": current_player.display_name,
        "is_muted": current_player.is_muted,
        "is_banned": current_player.is_banned
    }), 200

@auth_bp.route("/refresh", methods=["POST"])
@require_auth
def refresh(current_player):
    token = create_token(current_player.id)
    return jsonify({"token": token}), 200
