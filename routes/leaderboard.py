from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import PlayerStats, Player

leaderboard_bp = Blueprint("leaderboard", __name__)

@leaderboard_bp.route("/top", methods=["GET"])
@jwt_required()
def get_top():
    limit = int(request.args.get("limit", 50))
    stat = request.args.get("stat", "xp")
    allowed = ["xp", "games_played", "times_tagger", "level"]
    if stat not in allowed:
        stat = "xp"
    order_col = getattr(PlayerStats, stat)
    results = db.session.query(PlayerStats, Player).join(Player, PlayerStats.player_id == Player.id).filter(Player.is_banned == False).order_by(order_col.desc()).limit(limit).all()
    board = []
    for i, (stats, player) in enumerate(results):
        board.append({"rank": i + 1, "player_id": player.id, "display_name": player.display_name, "xp": stats.xp, "level": stats.level, "games_played": stats.games_played, "times_tagger": stats.times_tagger})
    return jsonify(board), 200

@leaderboard_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_stats():
    player_id = get_jwt_identity()
    stats = PlayerStats.query.filter_by(player_id=player_id).first()
    if not stats:
        return jsonify({"error": "Stats not found"}), 404
    return jsonify({"player_id": player_id, "xp": stats.xp, "level": stats.level, "games_played": stats.games_played, "times_tagged": stats.times_tagged, "times_tagger": stats.times_tagger, "total_playtime": stats.total_playtime}), 200

@leaderboard_bp.route("/update", methods=["POST"])
@jwt_required()
def update_stats():
    player_id = get_jwt_identity()
    data = request.get_json() or {}
    stats = PlayerStats.query.filter_by(player_id=player_id).first()
    if not stats:
        return jsonify({"error": "Stats not found"}), 404
    stats.games_played += data.get("games_played", 0)
    stats.times_tagged += data.get("times_tagged", 0)
    stats.times_tagger += data.get("times_tagger", 0)
    stats.total_playtime += data.get("playtime", 0)
    xp_gain = data.get("xp", 0)
    stats.xp += xp_gain
    stats.level = max(1, stats.xp // 1000 + 1)
    db.session.commit()
    return jsonify({"success": True, "xp": stats.xp, "level": stats.level}), 200
