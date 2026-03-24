from app import db
from datetime import datetime
import uuid

class Player(db.Model):
    __tablename__ = "players"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(64), nullable=False)
    platform = db.Column(db.String(32), default="quest")
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

class PlayerStats(db.Model):
    __tablename__ = "player_stats"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = db.Column(db.String(36), db.ForeignKey("players.id"), unique=True)
    games_played = db.Column(db.Integer, default=0)
    times_tagged = db.Column(db.Integer, default=0)
    times_tagger = db.Column(db.Integer, default=0)
    total_playtime = db.Column(db.Integer, default=0)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)

class Room(db.Model):
    __tablename__ = "rooms"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_code = db.Column(db.String(8), unique=True, nullable=False)
    host_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    region = db.Column(db.String(32), default="us-west")
    max_players = db.Column(db.Integer, default=10)
    current_players = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    game_mode = db.Column(db.String(32), default="infection")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    reported_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    reason = db.Column(db.String(256), nullable=False)
    room_id = db.Column(db.String(36), nullable=True)
    reviewed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AntiCheatLog(db.Model):
    __tablename__ = "anticheat_logs"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    violation_type = db.Column(db.String(64), nullable=False)
    details = db.Column(db.String(512), nullable=True)
    room_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
