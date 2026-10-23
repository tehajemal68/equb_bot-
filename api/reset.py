from api._common import *

class handler(HandlerBase):
    def do_POST(self):
        user = require_user(self)
        if not user: return
        if not is_admin(user):
            response(self, 403, {"error": "Administrator only"})
            return
        try:
            redis.set(STATE_KEY, json.dumps({"status": "waiting", "winner": None, "draw_id": 0, "started_at": None}))
            # Reset clears recent history as requested by the current frontend.
            redis.delete(HISTORY_KEY)
            response(self, 200, {"ok": True, "status": "waiting"})
        except Exception:
            response(self, 503, {"error": "Storage unavailable; reset did not complete"})
