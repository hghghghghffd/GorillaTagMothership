from flask import Blueprint, request, jsonify
from models import db, Room, Player
from utils.jwt_helper import require_auth
from utils.room_manager import RoomManager
import random
import string

matchmaking_bp = Blueprint("matchmaking", __name__)

def generate_room_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

@matchmaking_bp.route("/quickmatch", methods=["POST"])
@require_auth
def quickmatch(current_player):
    data = request.get_json() or {}
    region = data.get("region", "us-west")
    game_mode = data.get("game_mode", "infection")
    room = Room.query.filter_by(
        is_active=True,
        is_private=False,
        region=region,
        game_mode=game_mode
    ).filter(Room.max_players > RoomManager.get_player_count_for_rooms()).first()
    if not room:
        code = generate_room_code()
        while Room.query.filter_by(room_code=code).first():
            code = generate_room_code()
        room = Room(
            host_id=current_player.id,
            room_code=code,
            region=region,
            game_mode=game_mode,
            is_private=False
        )
        db.session.add(room)
        db.session.commit()
    return jsonify({
        "room_id": room.id,
        "room_code": room.room_code,
        "region": room.region,
        "game_mode": room.game_mode,
        "map_name": room.map_name
    }), 200

@matchmaking_bp.route("/create", methods=["POST"])
@require_auth
def create_room(current_player):
    data = request.get_json() or {}
    code = generate_room_code()
    while Room.query.filter_by(room_code=code).first():
        code = generate_room_code()
    room = Room(
        host_id=current_player.id,
        room_code=code,
        map_name=data.get("map_name", "default"),
        game_mode=data.get("game_mode", "infection"),
        is_private=data.get("is_private", False),
        max_players=min(data.get("max_players", 10), 10),
        region=data.get("region", "us-west")
    )
    db.session.add(room)
    db.session.commit()
    return jsonify({
        "room_id": room.id,
        "room_code": room.room_code,
        "region": room.region,
        "game_mode": room.game_mode
    }), 201

@matchmaking_bp.route("/join/<room_code>", methods=["POST"])
@require_auth
def join_room(current_player, room_code):
    room = Room.query.filter_by(room_code=room_code.upper(), is_active=True).first()
    if not room:
        return jsonify({"error": "Room not found"}), 404
    count = RoomManager.get_player_count(room.id)
    if count >= room.max_players:
        return jsonify({"error": "Room is full"}), 409
    return jsonify({
        "room_id": room.id,
        "room_code": room.room_code,
        "region": room.region,
        "game_mode": room.game_mode,
        "map_name": room.map_name,
        "player_count": count
    }), 200

@matchmaking_bp.route("/rooms", methods=["GET"])
@require_auth
def list_rooms(current_player):
    region = request.args.get("region", "us-west")
    rooms = Room.query.filter_by(is_active=True, is_private=False, region=region).all()
    result = []
    for room in rooms:
        count = RoomManager.get_player_count(room.id)
        if count < room.max_players:
            result.append({
                "room_id": room.id,
                "room_code": room.room_code,
                "game_mode": room.game_mode,
                "map_name": room.map_name,
                "player_count": count,
                "max_players": room.max_players
            })
    return jsonify({"rooms": result}), 200

@matchmaking_bp.route("/close/<room_id>", methods=["DELETE"])
@require_auth
def close_room(current_player, room_id):
    room = Room.query.filter_by(id=room_id, host_id=current_player.id).first()
    if not room:
        return jsonify({"error": "Room not found or not authorized"}), 404
    room.is_active = False
    db.session.commit()
    return jsonify({"success": True}), 200
