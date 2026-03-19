# 🤖 StrangerChat — Anonymous Telegram Bot

A production-ready, modular anonymous 1-on-1 chat bot built with **Python + aiogram 3**,
featuring onboarding, real-time matchmaking, Telegram Stars payments, and moderation.

---

## 📁 Project Structure

```
bot/
├── main.py                   # Entry point — wires everything together
├── config.py                 # Pydantic settings (loaded from .env)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── railway.toml              # Railway deploy config
├── render.yaml               # Render deploy config
├── .env.example
│
├── handlers/
│   ├── __init__.py
│   ├── onboarding.py         # /start + multi-step profile FSM
│   ├── menu.py               # Main menu callbacks
│   ├── chat.py               # Message relay + /next /stop /report
│   ├── payment.py            # PreCheckoutQuery + SuccessfulPayment
│   └── moderation.py         # Report logic + auto-ban helper
│
├── services/
│   ├── __init__.py
│   ├── state.py              # Async-safe in-memory state (BotState)
│   ├── matchmaking.py        # Queue management + partner matching
│   └── payments.py           # Telegram Stars invoice sender
│
└── utils/
    ├── __init__.py
    ├── messages.py           # All user-facing strings
    ├── keyboards.py          # InlineKeyboard factories
    ├── guards.py             # Reusable pre-condition checks
    └── scheduler.py          # Background task (idle timeout)
```

---

## ⚙️ Local Setup

### Prerequisites
- Python 3.11+
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/strangerchat-bot.git
cd strangerchat-bot/bot

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Open .env and set BOT_TOKEN=<your token>
```

### 3. Run

```bash
python main.py
```

---

## 🐳 Docker (Recommended)

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d --build

# View logs
docker compose logs -f bot

# Stop
docker compose down
```

---

## 🚀 Deployment

### Option A — Railway (Easiest)

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**
3. Select your repo
4. In **Variables**, add:
   ```
   BOT_TOKEN = your_token_here
   PAYMENT_PROVIDER_TOKEN = (leave empty for Stars)
   ```
5. Railway auto-detects `railway.toml` and deploys via Docker
6. ✅ Done — bot starts automatically

### Option B — Render

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New → Blueprint**
3. Connect your repo — Render reads `render.yaml`
4. Set `BOT_TOKEN` as a **secret environment variable** in the dashboard
5. Click **Apply** — deploys as a background Worker (no sleep!)

### Option C — VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update && sudo apt install -y python3.12 python3.12-venv git

# Clone repo
git clone https://github.com/YOUR_USERNAME/strangerchat-bot.git
cd strangerchat-bot/bot

# Setup
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env   # set BOT_TOKEN

# Run as a systemd service
sudo nano /etc/systemd/system/strangerchat.service
```

Paste this into the service file:
```ini
[Unit]
Description=StrangerChat Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/strangerchat-bot/bot
ExecStart=/home/ubuntu/strangerchat-bot/bot/venv/bin/python main.py
Restart=on-failure
RestartSec=5
EnvironmentFile=/home/ubuntu/strangerchat-bot/bot/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable strangerchat
sudo systemctl start strangerchat
sudo systemctl status strangerchat
```

---

## ⭐ Telegram Stars Payment Integration

### How it works

```
User taps "Gender Filter"
        ↓
Bot checks premium_status
        ↓ (not premium)
services/payments.py → bot.send_invoice(
    provider_token = "",      ← empty string = Telegram Stars
    currency       = "XTR",   ← Stars currency code
    amount         = 50       ← 50 Stars
)
        ↓
Telegram shows native payment UI
        ↓
handlers/payment.py → pre_checkout_query handler
    → query.answer(ok=True)   ← MUST respond within 10 seconds
        ↓
handlers/payment.py → successful_payment handler
    → state_store.set_premium(user_id)
        ↓
User can now use Gender Filter
```

### Key rules for Stars payments
| Rule | Value |
|------|-------|
| `provider_token` | `""` (empty string) |
| `currency` | `"XTR"` |
| Minimum amount | 1 XTR |
| Pre-checkout timeout | 10 seconds |
| Refunds | Via [@BotSupport](https://t.me/BotSupport) |

### Enabling payments on your bot
1. Open [@BotFather](https://t.me/BotFather)
2. `/mybots` → your bot → **Payments**
3. Select **Telegram Stars** as the provider
4. No additional setup needed — Stars work natively

---

## 🔄 User Flow

```
/start
  └─► Onboarding FSM
        1. Gender (inline buttons)
        2. Age (text, validated 13-100)
        3. Region (free text)
        4. Rules agreement (I Agree / I Decline)
              └─► Main Menu
                    ├── 🔍 Find Stranger ──► enqueue ──► match ──► relay chat
                    │                                         ├── /next (skip+rematch)
                    │                                         ├── /stop (end chat)
                    │                                         └── /report (flag + disconnect)
                    ├── ⭐ Gender Filter ──► check premium
                    │                         ├── NOT premium → Stars invoice
                    │                         └── IS premium  → choose filter → enqueue
                    ├── 👤 Profile ──► show profile card
                    └── 🚫 Report ──► report current partner
```

---

## 🛡️ Safety & Moderation

| Feature | Detail |
|---------|--------|
| Rate limiting | 20 messages / 10 seconds per user |
| Report system | 3 reports → auto temp-ban |
| Auto-ban | Reported user disconnected immediately |
| Rules gate | User must tap "I Agree" before any action |
| Idle timeout | 5-minute inactivity → auto-disconnect |
| Ban check | Banned users skipped during matchmaking |

---

## 📊 In-Memory Data Structures

```python
# All guarded by asyncio.Lock — zero race conditions
users:          dict[int, UserProfile]   # user_id → profile
waiting_queue:  list[QueueEntry]         # ordered by enqueue time
active_chats:   dict[int, int]           # user_id ↔ partner_id (both directions)
banned_users:   dict[int, BanRecord]
reports:        dict[int, list[int]]     # reported_id → [reporter_ids]
rate_limits:    dict[int, RateBucket]
last_activity:  dict[int, datetime]
```

---

## 📈 Scaling to Production (Redis + Database)

The in-memory architecture is intentional for simplicity, but when you outgrow one process:

### Step 1 — Redis for shared state

Replace `services/state.py` with Redis-backed equivalents:

```python
# pip install redis[asyncio]
import redis.asyncio as redis

r = redis.from_url("redis://localhost:6379")

# Queue → Redis List
await r.rpush("waiting_queue", user_id)
await r.lpop("waiting_queue")

# Active chats → Redis Hash
await r.hset("active_chats", user_id, partner_id)

# Rate limiting → Redis incr + expire
await r.incr(f"rate:{user_id}")
await r.expire(f"rate:{user_id}", 10)
```

Replace aiogram `MemoryStorage` with `RedisStorage`:
```python
from aiogram.fsm.storage.redis import RedisStorage
storage = RedisStorage.from_url("redis://localhost:6379")
```

### Step 2 — PostgreSQL for persistence

```python
# pip install asyncpg sqlalchemy[asyncio]
# Store user profiles and ban records permanently
# Use Alembic for migrations
```

### Step 3 — Horizontal scaling

Once Redis handles shared state, run multiple bot instances:
- Railway: increase replicas
- Render: enable auto-scaling
- VPS: use `gunicorn`-style process manager

### Step 4 — Webhook mode (optional, higher throughput)

```python
# In main.py replace start_polling with:
await dp.start_webhook(
    bot=bot,
    webhook_path="/webhook",
    host="0.0.0.0",
    port=8080,
)
```

### Recommended stack for 10k+ daily users

```
Telegram ──► Bot Instances (x3) ──► Redis Cluster
                                ──► PostgreSQL (read replica)
                                ──► Prometheus + Grafana (metrics)
```

---

## 🧪 Testing

```bash
# Unit test the state store (no Telegram needed)
python -m pytest tests/ -v

# Example test structure (create tests/ folder):
# tests/test_state.py   — matchmaking logic
# tests/test_payments.py — invoice payload validation
```

---

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | **required** | Telegram bot token from @BotFather |
| `PAYMENT_PROVIDER_TOKEN` | `""` | Empty for Stars; real token for card payments |
| `PREMIUM_STARS_PRICE` | `50` | Price in XTR (Telegram Stars) |
| `REPORTS_BEFORE_BAN` | `3` | Reports needed to auto-ban |
| `RATE_LIMIT_MESSAGES` | `20` | Max messages per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `10` | Rate limit window size |
| `CHAT_IDLE_TIMEOUT_SECONDS` | `300` | Idle chat auto-disconnect (5 min) |
| `SCHEDULER_INTERVAL_SECONDS` | `60` | Background task frequency |
| `MAX_QUEUE_WAIT_SECONDS` | `120` | Max queue wait before notification |

---

## 📄 License

MIT — free to use, modify, and deploy.
