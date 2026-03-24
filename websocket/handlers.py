from flask_socketio import emit, join_room, leave_room, disconnect
from flask import request
from models import db, Player, AntiCheatLog
from utils.jwt_helper import create_token
from utils.room_manager import RoomManager
from utils.anticheat import AntiCheat
from datetime import datetime
import jwt
import os

connected_players = {}

def register_handlers(socketio):

    def get_player_from_token(token):
        try:
            payload = jwt.decode(token, os.environ.get("JWT_SECRET", "changeme-jwt-secret"), algorithms=["HS256"])
            return Player.query.get(payload["sub"])
        except Exception:
            return None

    @socketio.on("connect")
    def on_connect():
        token = request.args.get("token")
        if not token:
            disconnect()
            return
        player = get_player_from_token(token)
        if not player or player.is_banned:
            disconnect()
            return
        connected_players[request.sid] = player.id
        emit("connected", {"player_id": player.id, "display_name": player.display_name})

    @socketio.on("disconnect")
    def on_disconnect():
        player_id = connected_players.pop(request.sid, None)
        if player_id:
            room_id = RoomManager.get_player_room(player_id)
            if room_id:
                leave_room(room_id)
                RoomManager.clear_player_room(player_id)
                emit("player_left", {"player_id": player_id}, to=room_id)

    @socketio.on("join_room")
    def on_join_room(data):
        player_id = connected_players.get(request.sid)
        if not player_id:
            return
        room_id = data.get("room_id")
        if not room_id:
            return
        count = RoomManager.get_player_count(room_id)
        if count >= 10:
            emit("error", {"message": "Room is full"})
            return
        RoomManager.add_player(room_id, player_id)
        RoomManager.set_player_room(player_id, room_id)
        join_room(room_id)
        player = Player.query.get(player_id)
        emit("player_joined", {
            "player_id": player_id,
            "display_name": player.display_name if player else "Unknown",
            "cosmetics": player.cosmetics if player else {}
        }, to=room_id)
        players = RoomManager.get_room_players(room_id)
        emit("room_state", {"players": [p.decode() if isinstance(p, bytes) else p for p in players]})

    @socketio.on("leave_room")
    def on_leave_room(data):
        player_id = connected_players.get(request.sid)
        if not player_id:
            return
        room_id = RoomManager.get_player_room(player_id)
        if room_id:
            leave_room(room_id)
            RoomManager.clear_player_room(player_id)
            emit("player_left", {"player_id": player_id}, to=room_id)

    @socketio.on("player_move")
    def on_player_move(data):
        player_id = connected_players.get(request.sid)
        if not player_id:
            return
        room_id = RoomManager.get_player_room(player_id)
        if not room_id:
            return
        position = data.get("position", {})
        rotation = data.get("rotation", {})
        velocity = data.get("velocity", {})
        prev_state = RoomManager.get_player_state(player_id)
        violation = AntiCheat.check_movement(prev_state, position, velocity)
        if violation:
            player = Player.query.get(player_id)
            if player:
                player.violation_count += 1
                log = AntiCheatLog(
                    player_id=player_id,
                    violation_type=violation["type"],
                    details=violation,
                    severity=violation.get("severity", "medium")
                )
                db.session.add(log)
                if player.violation_count >= 5:
                    player.is_banned = True
                    player.ban_reason = "Anti-cheat: movement violation"
                    from datetime import timedelta
                    player.ban_expires = datetime.utcnow() + timedelta(days=7)
                    db.session.commit()
                    emit("kicked", {"reason": "Anti-cheat violation"})
                    disconnect()
                    return
                db.session.commit()
        RoomManager.store_player_state(player_id, {"position": position, "timestamp": datetime.utcnow().timestamp()})
        emit("player_moved", {
            "player_id": player_id,
            "position": position,
            "rotation": rotation,
            "velocity": velocity
        }, to=room_id, include_self=False)

    @socketio.on("player_tagged")
    def on_player_tagged(data):
        player_id = connected_players.get(request.sid)
        if not player_id:
            return
        room_id = RoomManager.get_player_room(player_id)
        if not room_id:
            return
        tagged_id = data.get("tagged_id")
        if not tagged_id:
            return
        emit("tagged", {
            "tagger_id": player_id,
            "tagged_id": tagged_id,
            "timestamp": datetime.utcnow().isoformat()
        }, to=room_id)

    @socketio.on("chat_message")
    def on_chat(data):
        player_id = connected_players.get(request.sid)
        if not player_id:
            return
        player = Player.query.get(player_id)
        if not player or player.is_muted:
            emit("error", {"message": "You are muted"})
            return
        room_id = RoomManager.get_player_room(player_id)
        if not room_id:
            return
        message = str(data.get("message", ""))[:256].strip()
        if not message:
            return
        emit("chat", {
            "player_id": player_id,
            "display_name": player.display_name,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }, to=room_id)

    @socketio.on("ping")
    def on_ping():
        emit("pong", {"timestamp": datetime.utcnow().isoformat()})
