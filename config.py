import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "mothership-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "mothership-jwt-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://mothershipuser:GorillaTagsMothership103281790452603@18.118.102.219:5432/mothership")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {"connect_timeout": 10}
    }
    BACKEND_URL = os.environ.get("BACKEND_URL", "https://gorillatagsmothership.vercel.app")
    MAX_ROOM_SIZE = 10
    ANTICHEAT_SPEED_LIMIT = 20.0
    ANTICHEAT_TELEPORT_THRESHOLD = 50.0
    TOKEN_EXPIRE_HOURS = 24
