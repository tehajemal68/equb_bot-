import os, json, time, hmac, hashlib, urllib.parse
from http.server import BaseHTTPRequestHandler
from upstash_redis import Redis

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = os.environ.get("ADMIN_TELEGRAM_ID", "")
MAX_AUTH_AGE_SECONDS = int(os.environ.get("TELEGRAM_INITDATA_MAX_AGE", "3600"))
redis = Redis.from_env()

STATE_KEY = "halal-equb:state"
HISTORY_KEY = "halal-equb:history"
LOCK_KEY = "halal-equb:spin-lock"

def response(handler, status, payload):
    body = json.dumps(payload, separators=(",", ":")).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

def read_json(handler):
    try:
        length = int(handler.headers.get("Content-Length", "0"))
        if length > 16384:
            return {}
        return json.loads(handler.rfile.read(length) or b"{}")
    except Exception:
        return {}

def validate_init_data(raw):
    if not BOT_TOKEN or not raw or len(raw) > 10000:
        return None
    try:
        pairs = urllib.parse.parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
        values = dict(pairs)
        received_hash = values.pop("hash", None)
        values.pop("signature", None)
        if not received_hash:
            return None
        check_string = "\n".join(f"{k}={v}" for k, v in sorted(values.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, received_hash):
            return None
        auth_date = int(values.get("auth_date", "0"))
        now = int(time.time())
        if auth_date > now + 30 or now - auth_date > MAX_AUTH_AGE_SECONDS:
            return None
        user = json.loads(values.get("user", "{}"))
        user_id = user.get("id")
        if not isinstance(user_id, int):
            return None
        return {"id": user_id, "first_name": user.get("first_name", ""), "username": user.get("username", "")}
    except Exception:
        return None

def authenticated_user(handler):
    auth = handler.headers.get("Authorization", "")
    if not auth.startswith("tma "):
        return None
    return validate_init_data(auth[4:].strip())

def require_user(handler):
    user = authenticated_user(handler)
    if not user:
        response(handler, 401, {"error": "Invalid or expired Telegram authentication. Open this app from Telegram again."})
        return None
    return user

def is_admin(user):
    return bool(ADMIN_ID) and str(user["id"]) == ADMIN_ID

def get_state():
    raw = redis.get(STATE_KEY)
    if not raw:
        return {"status": "waiting", "winner": None, "draw_id": 0, "started_at": None}
    if isinstance(raw, dict):
        return raw
    return json.loads(raw)

def get_history():
    items = redis.lrange(HISTORY_KEY, 0, 49) or []
    result = []
    for item in items:
        if isinstance(item, dict):
            result.append(item)
        else:
            try: result.append(json.loads(item))
            except Exception: pass
    return result

class HandlerBase(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Keep logs free of request headers, which may contain Telegram init data.
        print("%s - %s" % (self.address_string(), fmt % args))
