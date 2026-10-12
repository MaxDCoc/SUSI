# --- Etapa 1: build del frontend ---
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Etapa 2: aplicación (Django + SPA compilado) ---
FROM python:3.13-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist ./frontend_dist
RUN DJANGO_DEBUG=1 python manage.py collectstatic --noinput \
    && useradd --create-home --shell /usr/sbin/nologin susi \
    && mkdir -p /data/media \
    && chown -R susi:susi /data/media
USER susi
EXPOSE 8000
# 1 worker + threads: el caché de agregados (en memoria) debe vivir en un solo proceso.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn susi.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 60"]
