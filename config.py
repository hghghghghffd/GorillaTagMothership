import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "changeme-super-secret")
    JWT_SECRET = os.environ.get("JWT_SECRET", "changeme-jwt-secret")
    JWT_EXPIRY = timedelta(hours=24)
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///mothership.db")
    MAX_ROOM_SIZE = int(os.environ.get("MAX_ROOM_SIZE", 10))
    ANTICHEAT_SPEED_LIMIT = float(os.environ.get("ANTICHEAT_SPEED_LIMIT", 15.0))
    ANTICHEAT_TELEPORT_THRESHOLD = float(os.environ.get("ANTICHEAT_TELEPORT_THRESHOLD", 20.0))
    ANTICHEAT_VIOLATION_BAN_THRESHOLD = int(os.environ.get("ANTICHEAT_VIOLATION_BAN_THRESHOLD", 5))
    VERSION = os.environ.get("GAME_VERSION", "1.0.0")
