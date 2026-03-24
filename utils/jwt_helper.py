import jwt
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from models import Player

def create_token(player_id: str) -> str:
    payload = {
        "sub": player_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return jsonify({"error": "Missing token"}), 401
        try:
            payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
            player = Player.query.get(payload["sub"])
            if not player:
                return jsonify({"error": "Player not found"}), 401
            if player.is_banned:
                if player.ban_expires and player.ban_expires < datetime.utcnow():
                    player.is_banned = False
                    from models import db
                    db.session.commit()
                else:
                    return jsonify({"error": "Account banned"}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(player, *args, **kwargs)
    return decorated
