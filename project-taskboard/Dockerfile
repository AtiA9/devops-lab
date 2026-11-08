# Stage 3 - TaskBoard API image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# dependencies first: this layer is reused from the cache until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# stage 8: do not run as root; /data is where the SQLite volume is mounted
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser /data
USER appuser

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "app.app:app"]
