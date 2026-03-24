from flask import Blueprint, request, jsonify
from models import db, Player, Report, AntiCheatLog
from utils.jwt_helper import require_auth
from datetime import datetime, timedelta

moderation_bp = Blueprint("moderation", __name__)

@moderation_bp.route("/report", methods=["POST"])
@require_auth
def report_player(current_player):
    data = request.get_json()
    if not data or not data.get("reported_id") or not data.get("reason"):
        return jsonify({"error": "Missing fields"}), 400
    reported = Player.query.get(data["reported_id"])
    if not reported:
        return jsonify({"error": "Player not found"}), 404
    if reported.id == current_player.id:
        return jsonify({"error": "Cannot report yourself"}), 400
    allowed_reasons = {"cheating", "harassment", "hate_speech", "exploiting", "spam", "other"}
    if data["reason"] not in allowed_reasons:
        return jsonify({"error": "Invalid reason"}), 400
    report = Report(
        reporter_id=current_player.id,
        reported_id=reported.id,
        reason=data["reason"],
        description=data.get("description", "")[:512]
    )
    db.session.add(report)
    report_count = Report.query.filter_by(reported_id=reported.id, resolved=False).count()
    if report_count >= 5:
        reported.violation_count += 1
        if reported.violation_count >= 5:
            reported.is_banned = True
            reported.ban_reason = "Automatic ban: multiple violations"
            reported.ban_expires = datetime.utcnow() + timedelta(days=7)
    db.session.commit()
    return jsonify({"success": True, "report_id": report.id}), 201

@moderation_bp.route("/anticheat/log", methods=["POST"])
@require_auth
def log_violation(current_player):
    data = request.get_json()
    if not data or not data.get("violation_type"):
        return jsonify({"error": "Missing violation_type"}), 400
    severity_map = {
        "speed_hack": "high",
        "teleport": "high",
        "fly_hack": "high",
        "position_spoof": "medium",
        "packet_spam": "low",
        "invalid_input": "low"
    }
    vtype = data["violation_type"]
    severity = severity_map.get(vtype, "low")
    log = AntiCheatLog(
        player_id=current_player.id,
        violation_type=vtype,
        details=data.get("details", {}),
        severity=severity
    )
    db.session.add(log)
    action = None
    if severity == "high":
        current_player.violation_count += 1
        if current_player.violation_count >= 3:
            current_player.is_banned = True
            current_player.ban_reason = f"Anti-cheat: {vtype}"
            current_player.ban_expires = datetime.utcnow() + timedelta(days=30)
            action = "banned"
        else:
            action = "warning"
    log.auto_action = action
    db.session.commit()
    return jsonify({"success": True, "action": action}), 200

@moderation_bp.route("/ban/<player_id>", methods=["POST"])
@require_auth
def ban_player(current_player, player_id):
    data = request.get_json() or {}
    target = Player.query.get(player_id)
    if not target:
        return jsonify({"error": "Player not found"}), 404
    days = data.get("days", 7)
    target.is_banned = True
    target.ban_reason = data.get("reason", "Banned by moderator")
    target.ban_expires = datetime.utcnow() + timedelta(days=days) if days > 0 else None
    db.session.commit()
    return jsonify({"success": True}), 200

@moderation_bp.route("/mute/<player_id>", methods=["POST"])
@require_auth
def mute_player(current_player, player_id):
    target = Player.query.get(player_id)
    if not target:
        return jsonify({"error": "Player not found"}), 404
    target.is_muted = True
    db.session.commit()
    return jsonify({"success": True}), 200

@moderation_bp.route("/unmute/<player_id>", methods=["POST"])
@require_auth
def unmute_player(current_player, player_id):
    target = Player.query.get(player_id)
    if not target:
        return jsonify({"error": "Player not found"}), 404
    target.is_muted = False
    db.session.commit()
    return jsonify({"success": True}), 200
