# ── STAAD.Pro Procurement API — Railway image ────────────────────────────────
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install dependencies first so the layer is cached across code changes
COPY staad_procurement/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source into /app so api/, src/ live directly under the WORKDIR
COPY staad_procurement/ ./

EXPOSE 8000

# Bind to Railway's injected $PORT, falling back to 8000 for local `docker run`.
# sh -c expands ${PORT} at container start (not build) time.
CMD ["sh", "-c", "echo \"Starting uvicorn on 0.0.0.0:${PORT:-8000}\" && exec uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=*"]
