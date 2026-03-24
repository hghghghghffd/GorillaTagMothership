from flask import Blueprint, request, jsonify
from models import db, Player, PlayerStats
from utils.jwt_helper import require_auth

leaderboard_bp = Blueprint("leaderboard", __name__)

@leaderboard_bp.route("/top", methods=["GET"])
@require_auth
def get_top(current_player):
    stat = request.args.get("stat", "xp")
    limit = min(int(request.args.get("limit", 50)), 100)
    allowed = {"xp", "level", "tags", "wins", "games_played"}
    if stat not in allowed:
        return jsonify({"error": "Invalid stat"}), 400
    col = getattr(PlayerStats, stat)
    results = db.session.query(Player, PlayerStats)\
        .join(PlayerStats, Player.id == PlayerStats.player_id)\
        .filter(Player.is_banned == False)\
        .order_by(col.desc())\
        .limit(limit).all()
    board = []
    for rank, (player, stats) in enumerate(results, 1):
        board.append({
            "rank": rank,
            "player_id": player.id,
            "display_name": player.display_name,
            "value": getattr(stats, stat),
            "level": stats.level
        })
    return jsonify({"leaderboard": board, "stat": stat}), 200

@leaderboard_bp.route("/me", methods=["GET"])
@require_auth
def get_my_stats(current_player):
    stats = PlayerStats.query.filter_by(player_id=current_player.id).first()
    if not stats:
        return jsonify({"error": "Stats not found"}), 404
    return jsonify({
        "player_id": current_player.id,
        "display_name": current_player.display_name,
        "xp": stats.xp,
        "level": stats.level,
        "games_played": stats.games_played,
        "wins": stats.wins,
        "losses": stats.losses,
        "tags": stats.tags,
        "time_as_it": stats.time_as_it
    }), 200

@leaderboard_bp.route("/update", methods=["POST"])
@require_auth
def update_stats(current_player):
    data = request.get_json() or {}
    stats = PlayerStats.query.filter_by(player_id=current_player.id).first()
    if not stats:
        return jsonify({"error": "Stats not found"}), 404
    if "xp" in data:
        stats.xp += int(data["xp"])
        stats.level = max(1, stats.xp // 1000 + 1)
    if "games_played" in data:
        stats.games_played += 1
    if "win" in data and data["win"]:
        stats.wins += 1
    elif "win" in data and not data["win"]:
        stats.losses += 1
    if "tags" in data:
        stats.tags += int(data["tags"])
    if "time_as_it" in data:
        stats.time_as_it += float(data["time_as_it"])
    db.session.commit()
    return jsonify({"success": True, "level": stats.level, "xp": stats.xp}), 200
