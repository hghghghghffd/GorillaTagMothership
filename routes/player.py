from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Player, PlayerStats

player_bp = Blueprint("player", __name__)

@player_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    player_id = get_jwt_identity()
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Not found"}), 404
    stats = PlayerStats.query.filter_by(player_id=player_id).first()
    return jsonify({"player_id": player.id, "username": player.username, "display_name": player.display_name, "platform": player.platform, "created_at": player.created_at.isoformat(), "stats": {"xp": stats.xp if stats else 0, "level": stats.level if stats else 1, "games_played": stats.games_played if stats else 0}}), 200

@player_bp.route("/profile/<player_id>", methods=["GET"])
@jwt_required()
def get_player_profile(player_id):
    player = Player.query.get(player_id)
    if not player or player.is_banned:
        return jsonify({"error": "Not found"}), 404
    stats = PlayerStats.query.filter_by(player_id=player_id).first()
    return jsonify({"player_id": player.id, "display_name": player.display_name, "platform": player.platform, "stats": {"xp": stats.xp if stats else 0, "level": stats.level if stats else 1, "games_played": stats.games_played if stats else 0}}), 200

@player_bp.route("/profile/update", methods=["PUT"])
@jwt_required()
def update_profile():
    player_id = get_jwt_identity()
    data = request.get_json() or {}
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Not found"}), 404
    if "display_name" in data:
        player.display_name = data["display_name"][:64]
    db.session.commit()
    return jsonify({"success": True}), 200

@player_bp.route("/search", methods=["GET"])
@jwt_required()
def search_players():
    q = request.args.get("q", "")
    if len(q) < 2:
        return jsonify([]), 200
    players = Player.query.filter(Player.display_name.ilike(f"%{q}%"), Player.is_banned == False).limit(20).all()
    return jsonify([{"player_id": p.id, "display_name": p.display_name, "platform": p.platform} for p in players]), 200
