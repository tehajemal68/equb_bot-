from api._common import *

class handler(HandlerBase):
    def do_POST(self):
        user = require_user(self)
        if not user: return
        response(self, 200, {"ok": True, "user_id": user["id"], "is_admin": is_admin(user)})
