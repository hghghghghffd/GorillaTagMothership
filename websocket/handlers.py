from flask_socketio import emit, join_room, leave_room, disconnect
from flask_jwt_extended import decode_token
from app import db
from models import Player, Room, AntiCheatLog
from utils.anticheat import AntiCheatEngine
import time

anticheat = AntiCheatEngine()
player_positions = {}
player_rooms = {}

def register_handlers(socketio):

    @socketio.on("connect")
    def on_connect(auth):
        if not auth or not auth.get("token"):
            disconnect()
            return
        try:
            data = decode_token(auth["token"])
            player_id = data["sub"]
            player = Player.query.get(player_id)
            if not player or player.is_banned:
                disconnect()
                return
        except Exception:
            disconnect()

    @socketio.on("join_room")
    def on_join_room(data):
        if not data or not data.get("room_id") or not data.get("player_id"):
            return
        room_id = data["room_id"]
        player_id = data["player_id"]
        player_rooms[player_id] = room_id
        join_room(room_id)
        emit("player_joined", {"player_id": player_id, "display_name": data.get("display_name", "Player")}, to=room_id, include_self=False)

    @socketio.on("leave_room")
    def on_leave_room(data):
        if not data or not data.get("room_id") or not data.get("player_id"):
            return
        room_id = data["room_id"]
        player_id = data["player_id"]
        player_rooms.pop(player_id, None)
        player_positions.pop(player_id, None)
        leave_room(room_id)
        emit("player_left", {"player_id": player_id}, to=room_id)

    @socketio.on("player_move")
    def on_player_move(data):
        if not data or not data.get("player_id"):
            return
        player_id = data["player_id"]
        position = data.get("position", {})
        room_id = player_rooms.get(player_id)
        if not room_id:
            return
        violation = anticheat.check_movement(player_id, position, player_positions.get(player_id), time.time())
        if violation:
            log = AntiCheatLog(player_id=player_id, violation_type=violation["type"], details=violation["details"], room_id=room_id)
            db.session.add(log)
            db.session.commit()
            emit("anticheat_warning", {"player_id": player_id, "violation": violation["type"]}, to=room_id)
            return
        player_positions[player_id] = {"position": position, "timestamp": time.time()}
        emit("player_moved", {"player_id": player_id, "position": position, "rotation": data.get("rotation", {})}, to=room_id, include_self=False)

    @socketio.on("player_tagged")
    def on_player_tagged(data):
        if not data or not data.get("tagger_id") or not data.get("tagged_id"):
            return
        room_id = player_rooms.get(data["tagger_id"])
        if not room_id:
            return
        emit("tag_event", {"tagger_id": data["tagger_id"], "tagged_id": data["tagged_id"], "timestamp": time.time()}, to=room_id)

    @socketio.on("chat_message")
    def on_chat(data):
        if not data or not data.get("player_id") or not data.get("message"):
            return
        room_id = player_rooms.get(data["player_id"])
        if not room_id:
            return
        message = data["message"][:256]
        emit("chat", {"player_id": data["player_id"], "display_name": data.get("display_name", "Player"), "message": message}, to=room_id)

    @socketio.on("game_state")
    def on_game_state(data):
        if not data or not data.get("room_id"):
            return
        emit("game_state_update", data, to=data["room_id"], include_self=False)

    @socketio.on("disconnect")
    def on_disconnect():
        pass
