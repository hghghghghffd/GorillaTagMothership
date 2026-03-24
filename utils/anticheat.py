import math

SPEED_LIMIT = 20.0
TELEPORT_THRESHOLD = 50.0

class AntiCheatEngine:

    def check_movement(self, player_id, new_pos, last_data, current_time):
        if not last_data or not new_pos:
            return None
        last_pos = last_data.get("position", {})
        last_time = last_data.get("timestamp", current_time)
        dt = current_time - last_time
        if dt <= 0:
            return None
        dx = new_pos.get("x", 0) - last_pos.get("x", 0)
        dy = new_pos.get("y", 0) - last_pos.get("y", 0)
        dz = new_pos.get("z", 0) - last_pos.get("z", 0)
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist > TELEPORT_THRESHOLD:
            return {"type": "teleport", "details": f"Moved {dist:.2f} units instantly"}
        speed = dist / dt
        if speed > SPEED_LIMIT:
            return {"type": "speed_hack", "details": f"Speed {speed:.2f} exceeds limit {SPEED_LIMIT}"}
        return None

    def check_tag(self, tagger_pos, tagged_pos, tag_range=2.0):
        if not tagger_pos or not tagged_pos:
            return False
        dx = tagger_pos.get("x", 0) - tagged_pos.get("x", 0)
        dy = tagger_pos.get("y", 0) - tagged_pos.get("y", 0)
        dz = tagger_pos.get("z", 0) - tagged_pos.get("z", 0)
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        return dist <= tag_range
