import sys
import os
import logging

sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(level=logging.DEBUG)

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
jwt = JWTManager(app)

from routes.auth import auth_bp
from routes.matchmaking import matchmaking_bp
from routes.leaderboard import leaderboard_bp
from routes.moderation import moderation_bp
from routes.player import player_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(matchmaking_bp, url_prefix="/api/matchmaking")
app.register_blueprint(leaderboard_bp, url_prefix="/api/leaderboard")
app.register_blueprint(moderation_bp, url_prefix="/api/moderation")
app.register_blueprint(player_bp, url_prefix="/api/player")

@app.route("/")
def index():
    return jsonify({"status": "Mothership API online", "version": "1.0.0"})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

try:
    with app.app_context():
        db.create_all()
except Exception as e:
    logging.error(f"DB init failed: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
