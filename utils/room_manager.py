import redis
import json
from flask import current_app

class RoomManager:
    _redis = None

    @classmethod
    def _get_redis(cls):
        if cls._redis is None:
            cls._redis = redis.from_url(current_app.config["REDIS_URL"])
        return cls._redis

    @classmethod
    def get_player_count(cls, room_id: str) -> int:
        try:
            r = cls._get_redis()
            return r.scard(f"room:{room_id}:players")
        except Exception:
            return 0

    @classmethod
    def get_player_count_for_rooms(cls):
        return 0

    @classmethod
    def add_player(cls, room_id: str, player_id: str):
        try:
            r = cls._get_redis()
            r.sadd(f"room:{room_id}:players", player_id)
            r.expire(f"room:{room_id}:players", 3600)
        except Exception:
            pass

    @classmethod
    def remove_player(cls, room_id: str, player_id: str):
        try:
            r = cls._get_redis()
            r.srem(f"room:{room_id}:players", player_id)
        except Exception:
            pass

    @classmethod
    def get_room_players(cls, room_id: str):
        try:
            r = cls._get_redis()
            return list(r.smembers(f"room:{room_id}:players"))
        except Exception:
            return []

    @classmethod
    def set_player_room(cls, player_id: str, room_id: str):
        try:
            r = cls._get_redis()
            r.set(f"player:{player_id}:room", room_id, ex=3600)
        except Exception:
            pass

    @classmethod
    def get_player_room(cls, player_id: str):
        try:
            r = cls._get_redis()
            val = r.get(f"player:{player_id}:room")
            return val.decode() if val else None
        except Exception:
            return None

    @classmethod
    def clear_player_room(cls, player_id: str):
        try:
            r = cls._get_redis()
            room_id = cls.get_player_room(player_id)
            if room_id:
                cls.remove_player(room_id, player_id)
            r.delete(f"player:{player_id}:room")
        except Exception:
            pass

    @classmethod
    def store_player_state(cls, player_id: str, state: dict):
        try:
            r = cls._get_redis()
            r.set(f"player:{player_id}:state", json.dumps(state), ex=60)
        except Exception:
            pass

    @classmethod
    def get_player_state(cls, player_id: str):
        try:
            r = cls._get_redis()
            val = r.get(f"player:{player_id}:state")
            return json.loads(val) if val else None
        except Exception:
            return None
