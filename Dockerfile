FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx supervisor && \
    rm -rf /var/lib/apt/lists/*

# --- Backend ---
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# --- Frontend ---
COPY frontend/ /usr/share/nginx/html

# --- Config ---
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY supervisord.conf /etc/supervisor/conf.d/app.conf

RUN rm -f /etc/nginx/sites-enabled/default

EXPOSE 80

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/app.conf"]
