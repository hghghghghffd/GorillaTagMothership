from flask import Blueprint, request, jsonify
from models import db, Player, PlayerStats
from utils.jwt_helper import require_auth

player_bp = Blueprint("player", __name__)

@player_bp.route("/profile/<player_id>", methods=["GET"])
@require_auth
def get_profile(current_player, player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404
    stats = PlayerStats.query.filter_by(player_id=player.id).first()
    return jsonify({
        "player_id": player.id,
        "display_name": player.display_name,
        "created_at": player.created_at.isoformat(),
        "last_seen": player.last_seen.isoformat(),
        "cosmetics": player.cosmetics,
        "stats": {
            "xp": stats.xp if stats else 0,
            "level": stats.level if stats else 1,
            "games_played": stats.games_played if stats else 0,
            "wins": stats.wins if stats else 0,
            "tags": stats.tags if stats else 0
        }
    }), 200

@player_bp.route("/cosmetics", methods=["PUT"])
@require_auth
def update_cosmetics(current_player):
    data = request.get_json() or {}
    allowed_keys = {"hat", "face", "badge", "color", "holdable"}
    filtered = {k: v for k, v in data.items() if k in allowed_keys}
    current_player.cosmetics = {**current_player.cosmetics, **filtered}
    db.session.commit()
    return jsonify({"success": True, "cosmetics": current_player.cosmetics}), 200

@player_bp.route("/search", methods=["GET"])
@require_auth
def search_player(current_player):
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify({"error": "Query too short"}), 400
    players = Player.query.filter(
        Player.display_name.ilike(f"%{query}%"),
        Player.is_banned == False
    ).limit(10).all()
    return jsonify({
        "results": [{"player_id": p.id, "display_name": p.display_name} for p in players]
    }), 200
