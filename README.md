# HALAL EQUB — Vercel starter

## Files
- `index.html`: Telegram Mini App frontend, updated to send Telegram's signed `initData`.
- `api/auth.py`: validates Telegram init data and returns admin status.
- `api/spin.py`: server-side winner selection; admin only.
- `api/reset.py`: admin-only reset.
- `api/status.py`: current draw and recent history.
- `api/_common.py`: shared auth and Redis helpers.
- `requirements.txt`: Upstash Redis client.

## Before deployment
1. Create/link this folder as the Vercel project root for `equb-lottery.vercel.app`.
2. In Vercel Marketplace, add an Upstash Redis database to this project. Ensure `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` exist in Production environment variables.
3. In Vercel Project → Settings → Environment Variables, add:
   - `TELEGRAM_BOT_TOKEN`: the bot token from BotFather (secret; never put it in HTML/GitHub).
   - `ADMIN_TELEGRAM_ID`: your numeric Telegram user ID (not username).
   - Optional `TELEGRAM_INITDATA_MAX_AGE`: `3600` (seconds).
4. Redeploy after adding variables.
5. In BotFather, set the Mini App URL to `https://equb-lottery.vercel.app` (or configure the bot menu button to that URL).
6. Open the app from Telegram, not by opening the URL directly. Direct browser access is intentionally unauthenticated.

## API response contract
- `POST /api/auth` with `Authorization: tma <Telegram.WebApp.initData>`
- `POST /api/spin` with same header (admin only)
- `POST /api/reset` with same header (admin only)
- `GET /api/status` with same header

## Important notes
- Do not add the bot token or Redis credentials to frontend code.
- Set `ADMIN_TELEGRAM_ID` to your own numeric Telegram user ID.
- This starter records draws and clears history when admin uses Reset. Export/back up history before resetting if you need an audit trail.
- Test with small non-monetary draws first. For real-money or regulated lotteries, check applicable local laws and use an independently auditable draw process.
- This is a starter implementation; do a security and concurrency review before using it for consequential or paid draws.
