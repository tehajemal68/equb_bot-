from api._common import *

class handler(HandlerBase):
    def do_GET(self):
        user = require_user(self)
        if not user: return
        try:
            state = get_state()
            status = state.get("status", "waiting")
            if status == "spinning" and state.get("started_at") and int(time.time()) - int(state["started_at"]) >= 6:
                state["status"] = "finished"
                redis.set(STATE_KEY, json.dumps(state))
                status = "finished"
            response(self, 200, {
                "status": status,
                "winner": state.get("winner"),
                "draw_id": state.get("draw_id", 0),
                "history": get_history()
            })
        except Exception:
            response(self, 503, {"error": "Storage unavailable"})
