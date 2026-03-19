# ─────────────────────────────────────────────────────────────
# Dockerfile — StrangerChat Telegram Bot
# Multi-stage build for a lean production image
# ─────────────────────────────────────────────────────────────

# ── Stage 1: dependency installer ─────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /install

COPY requirements.txt .
RUN pip install --prefix=/install/deps --no-cache-dir -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────
FROM python:3.12-slim

# Non-root user for security
RUN addgroup --system bot && adduser --system --ingroup bot bot

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install/deps /usr/local

# Copy application source
COPY --chown=bot:bot . .

USER bot

# Telegram bots use long-polling — no port needed
CMD ["python", "-u", "main.py"]
