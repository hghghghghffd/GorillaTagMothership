from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Room, Player
import random
import string

matchmaking_bp = Blueprint("matchmaking", __name__)

def generate_room_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@matchmaking_bp.route("/create", methods=["POST"])
@jwt_required()
def create_room():
    player_id = get_jwt_identity()
    data = request.get_json() or {}
    code = generate_room_code()
    while Room.query.filter_by(room_code=code, is_active=True).first():
        code = generate_room_code()
    room = Room(
        room_code=code,
        host_id=player_id,
        region=data.get("region", "us-west"),
        max_players=data.get("max_players", 10),
        game_mode=data.get("game_mode", "infection"),
        current_players=1
    )
    db.session.add(room)
    db.session.commit()
    return jsonify({"room_id": room.id, "room_code": room.room_code, "region": room.region, "game_mode": room.game_mode}), 201

@matchmaking_bp.route("/join", methods=["POST"])
@jwt_required()
def join_room():
    data = request.get_json()
    if not data or not data.get("room_code"):
        return jsonify({"error": "Room code required"}), 400
    room = Room.query.filter_by(room_code=data["room_code"], is_active=True).first()
    if not room:
        return jsonify({"error": "Room not found"}), 404
    if room.current_players >= room.max_players:
        return jsonify({"error": "Room full"}), 409
    room.current_players += 1
    db.session.commit()
    return jsonify({"room_id": room.id, "room_code": room.room_code, "region": room.region, "game_mode": room.game_mode, "players": room.current_players}), 200

@matchmaking_bp.route("/quickjoin", methods=["POST"])
@jwt_required()
def quick_join():
    data = request.get_json() or {}
    region = data.get("region", "us-west")
    game_mode = data.get("game_mode", "infection")
    room = Room.query.filter_by(region=region, game_mode=game_mode, is_active=True).filter(Room.current_players < Room.max_players).order_by(Room.current_players.desc()).first()
    if not room:
        player_id = get_jwt_identity()
        code = generate_room_code()
        while Room.query.filter_by(room_code=code, is_active=True).first():
            code = generate_room_code()
        room = Room(room_code=code, host_id=player_id, region=region, game_mode=game_mode, current_players=1)
        db.session.add(room)
        db.session.commit()
        return jsonify({"room_id": room.id, "room_code": room.room_code, "created": True}), 201
    room.current_players += 1
    db.session.commit()
    return jsonify({"room_id": room.id, "room_code": room.room_code, "created": False, "players": room.current_players}), 200

@matchmaking_bp.route("/leave", methods=["POST"])
@jwt_required()
def leave_room():
    data = request.get_json()
    if not data or not data.get("room_id"):
        return jsonify({"error": "Room ID required"}), 400
    room = Room.query.get(data["room_id"])
    if not room:
        return jsonify({"error": "Room not found"}), 404
    if room.current_players > 0:
        room.current_players -= 1
    if room.current_players == 0:
        room.is_active = False
    db.session.commit()
    return jsonify({"success": True}), 200

@matchmaking_bp.route("/rooms", methods=["GET"])
@jwt_required()
def list_rooms():
    region = request.args.get("region")
    query = Room.query.filter_by(is_active=True)
    if region:
        query = query.filter_by(region=region)
    rooms = query.filter(Room.current_players < Room.max_players).all()
    return jsonify([{"room_id": r.id, "room_code": r.room_code, "region": r.region, "game_mode": r.game_mode, "players": r.current_players, "max_players": r.max_players} for r in rooms]), 200
