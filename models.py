from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Player(db.Model):
    __tablename__ = "players"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(256), nullable=True)
    ban_expires = db.Column(db.DateTime, nullable=True)
    is_muted = db.Column(db.Boolean, default=False)
    violation_count = db.Column(db.Integer, default=0)
    cosmetics = db.Column(db.JSON, default=dict)
    stats = db.relationship("PlayerStats", uselist=False, back_populates="player")
    reports_made = db.relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter")
    reports_received = db.relationship("Report", foreign_keys="Report.reported_id", back_populates="reported")

class PlayerStats(db.Model):
    __tablename__ = "player_stats"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = db.Column(db.String(36), db.ForeignKey("players.id"), unique=True)
    player = db.relationship("Player", back_populates="stats")
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    games_played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    tags = db.Column(db.Integer, default=0)
    time_as_it = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Room(db.Model):
    __tablename__ = "rooms"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_code = db.Column(db.String(8), unique=True, nullable=False)
    host_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    map_name = db.Column(db.String(64), default="default")
    game_mode = db.Column(db.String(32), default="infection")
    is_private = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    max_players = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    region = db.Column(db.String(32), default="us-west")

class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    reported_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    reporter = db.relationship("Player", foreign_keys=[reporter_id], back_populates="reports_made")
    reported = db.relationship("Player", foreign_keys=[reported_id], back_populates="reports_received")
    reason = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)

class AntiCheatLog(db.Model):
    __tablename__ = "anticheat_logs"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = db.Column(db.String(36), db.ForeignKey("players.id"))
    violation_type = db.Column(db.String(64), nullable=False)
    details = db.Column(db.JSON, default=dict)
    severity = db.Column(db.String(16), default="low")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    auto_action = db.Column(db.String(32), nullable=True)
