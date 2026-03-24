from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config
from routes.auth import auth_bp
from routes.matchmaking import matchmaking_bp
from routes.leaderboard import leaderboard_bp
from routes.moderation import moderation_bp
from routes.player import player_bp
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(matchmaking_bp, url_prefix="/api/matchmaking")
app.register_blueprint(leaderboard_bp, url_prefix="/api/leaderboard")
app.register_blueprint(moderation_bp, url_prefix="/api/moderation")
app.register_blueprint(player_bp, url_prefix="/api/player")

from websocket.handlers import register_handlers
register_handlers(socketio)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
