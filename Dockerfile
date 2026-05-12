# ── STAAD.Pro Procurement API — Railway image ────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so the layer is cached across code changes
COPY staad_procurement/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend source
COPY staad_procurement/ /app/staad_procurement/

WORKDIR /app/staad_procurement

# Railway injects PORT at runtime; default to 8000 for local `docker run`
ENV PORT=8000
EXPOSE 8000

# Use sh -c so $PORT is expanded at container start time, not build time.
# Echo the chosen port so it's visible in Railway's deploy logs.
CMD ["sh", "-c", "echo \"Starting uvicorn on 0.0.0.0:${PORT}\" && exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
