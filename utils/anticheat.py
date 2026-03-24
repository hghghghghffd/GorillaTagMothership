import math
from datetime import datetime

class AntiCheat:
    SPEED_LIMIT = 15.0
    TELEPORT_THRESHOLD = 20.0
    MAX_VELOCITY = 30.0

    @staticmethod
    def check_movement(prev_state, position, velocity):
        if not prev_state or not position:
            return None
        prev_pos = prev_state.get("position", {})
        prev_time = prev_state.get("timestamp", datetime.utcnow().timestamp())
        now = datetime.utcnow().timestamp()
        dt = now - prev_time
        if dt <= 0:
            return None
        px = position.get("x", 0)
        py = position.get("y", 0)
        pz = position.get("z", 0)
        ox = prev_pos.get("x", px)
        oy = prev_pos.get("y", py)
        oz = prev_pos.get("z", pz)
        dist = math.sqrt((px - ox)**2 + (py - oy)**2 + (pz - oz)**2)
        speed = dist / dt if dt > 0 else 0
        if dist > AntiCheat.TELEPORT_THRESHOLD:
            return {"type": "teleport", "severity": "high", "distance": dist}
        if speed > AntiCheat.SPEED_LIMIT:
            return {"type": "speed_hack", "severity": "high", "speed": speed}
        if velocity:
            vx = velocity.get("x", 0)
            vy = velocity.get("y", 0)
            vz = velocity.get("z", 0)
            vmag = math.sqrt(vx**2 + vy**2 + vz**2)
            if vmag > AntiCheat.MAX_VELOCITY:
                return {"type": "invalid_velocity", "severity": "medium", "velocity": vmag}
        return None

    @staticmethod
    def validate_position(position):
        if not position:
            return False
        for key in ("x", "y", "z"):
            val = position.get(key, 0)
            if not isinstance(val, (int, float)):
                return False
            if abs(val) > 10000:
                return False
        return True
