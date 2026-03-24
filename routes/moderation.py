from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Report, Player, AntiCheatLog

moderation_bp = Blueprint("moderation", __name__)

@moderation_bp.route("/report", methods=["POST"])
@jwt_required()
def report_player():
    reporter_id = get_jwt_identity()
    data = request.get_json()
    if not data or not data.get("reported_id") or not data.get("reason"):
        return jsonify({"error": "Missing fields"}), 400
    if reporter_id == data["reported_id"]:
        return jsonify({"error": "Cannot report yourself"}), 400
    report = Report(
        reporter_id=reporter_id,
        reported_id=data["reported_id"],
        reason=data["reason"],
        room_id=data.get("room_id")
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"success": True, "report_id": report.id}), 201

@moderation_bp.route("/ban", methods=["POST"])
@jwt_required()
def ban_player():
    data = request.get_json()
    if not data or not data.get("player_id") or not data.get("reason"):
        return jsonify({"error": "Missing fields"}), 400
    player = Player.query.get(data["player_id"])
    if not player:
        return jsonify({"error": "Player not found"}), 404
    player.is_banned = True
    player.ban_reason = data["reason"]
    db.session.commit()
    return jsonify({"success": True}), 200

@moderation_bp.route("/unban", methods=["POST"])
@jwt_required()
def unban_player():
    data = request.get_json()
    if not data or not data.get("player_id"):
        return jsonify({"error": "Missing player_id"}), 400
    player = Player.query.get(data["player_id"])
    if not player:
        return jsonify({"error": "Player not found"}), 404
    player.is_banned = False
    player.ban_reason = None
    db.session.commit()
    return jsonify({"success": True}), 200

@moderation_bp.route("/reports", methods=["GET"])
@jwt_required()
def get_reports():
    reviewed = request.args.get("reviewed", "false").lower() == "true"
    reports = Report.query.filter_by(reviewed=reviewed).order_by(Report.created_at.desc()).limit(100).all()
    return jsonify([{"report_id": r.id, "reporter_id": r.reporter_id, "reported_id": r.reported_id, "reason": r.reason, "room_id": r.room_id, "created_at": r.created_at.isoformat()} for r in reports]), 200

@moderation_bp.route("/anticheat/logs", methods=["GET"])
@jwt_required()
def get_anticheat_logs():
    player_id = request.args.get("player_id")
    query = AntiCheatLog.query
    if player_id:
        query = query.filter_by(player_id=player_id)
    logs = query.order_by(AntiCheatLog.created_at.desc()).limit(200).all()
    return jsonify([{"id": l.id, "player_id": l.player_id, "violation_type": l.violation_type, "details": l.details, "room_id": l.room_id, "created_at": l.created_at.isoformat()} for l in logs]), 200
