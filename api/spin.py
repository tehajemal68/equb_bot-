from api._common import *
import secrets

class handler(HandlerBase):
    def do_POST(self):
        user = require_user(self)
        if not user: return
        if not is_admin(user):
            response(self, 403, {"error": "Administrator only"})
            return
        try:
            # Short Redis lock prevents two nearly simultaneous spin requests.
            if not redis.set(LOCK_KEY, str(user["id"]), nx=True, ex=10):
                response(self, 409, {"error": "A draw is already being started"})
                return
            try:
                previous = get_state()
                draw_id = int(previous.get("draw_id", 0)) + 1
                winner = secrets.randbelow(100) + 1
                started_at = int(time.time())
                state = {"status": "spinning", "winner": winner, "draw_id": draw_id, "started_at": started_at}
                redis.set(STATE_KEY, json.dumps(state))
                item = {"winner": winner, "draw_id": draw_id, "time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(started_at))}
                redis.lpush(HISTORY_KEY, json.dumps(item))
                redis.ltrim(HISTORY_KEY, 0, 49)
                response(self, 200, {"ok": True, **state})
            finally:
                redis.delete(LOCK_KEY)
        except Exception:
            response(self, 503, {"error": "Storage unavailable; no draw was confirmed"})
