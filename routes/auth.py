from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import Player, PlayerStats
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password") or not data.get("display_name"):
        return jsonify({"error": "Missing required fields"}), 400
    if Player.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 409
    player = Player(
        username=data["username"],
        password_hash=generate_password_hash(data["password"]),
        display_name=data["display_name"],
        platform=data.get("platform", "quest")
    )
    db.session.add(player)
    db.session.flush()
    stats = PlayerStats(player_id=player.id)
    db.session.add(stats)
    db.session.commit()
    token = create_access_token(identity=player.id, expires_delta=timedelta(hours=24))
    return jsonify({"token": token, "player_id": player.id, "display_name": player.display_name}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "Missing credentials"}), 400
    player = Player.query.filter_by(username=data["username"]).first()
    if not player or not check_password_hash(player.password_hash, data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401
    if player.is_banned:
        return jsonify({"error": "Account banned", "reason": player.ban_reason}), 403
    player.last_login = datetime.utcnow()
    db.session.commit()
    token = create_access_token(identity=player.id, expires_delta=timedelta(hours=24))
    return jsonify({"token": token, "player_id": player.id, "display_name": player.display_name}), 200

@auth_bp.route("/validate", methods=["GET"])
@jwt_required()
def validate():
    player_id = get_jwt_identity()
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    if player.is_banned:
        return jsonify({"error": "Account banned", "reason": player.ban_reason}), 403
    return jsonify({"valid": True, "player_id": player.id, "display_name": player.display_name}), 200

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    return jsonify({"success": True}), 200
