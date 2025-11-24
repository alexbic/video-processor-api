FROM python:3.11-slim

WORKDIR /app

# ===== СЛОЙ 1: Системные зависимости (редко меняются) =====
RUN apt-get update && apt-get install -y \
    ffmpeg \
    redis-server \
    supervisor \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# ===== СЛОЙ 2: Python зависимости (меняются редко) =====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== СЛОЙ 3: Директории и шрифты (редко меняются) =====
RUN mkdir -p /app/fonts /app/tasks /var/log/supervisor /var/run/supervisor
COPY fonts/ /app/fonts/

# ===== СЛОЙ 4: Конфигурация fontconfig (не меняется) =====
RUN mkdir -p /etc/fonts/conf.d && \
    echo '<?xml version="1.0"?>' > /etc/fonts/local.conf && \
    echo '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">' >> /etc/fonts/local.conf && \
    echo '<fontconfig>' >> /etc/fonts/local.conf && \
    echo '  <dir>/app/fonts</dir>' >> /etc/fonts/local.conf && \
    echo '</fontconfig>' >> /etc/fonts/local.conf && \
    fc-cache -fv /app/fonts

# ===== СЛОЙ 5: Supervisor конфиг (не меняется часто) =====
RUN echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:redis]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru --save ""' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:gunicorn]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=gunicorn --logger-class gunicorn_config.CustomLogger --preload --bind 0.0.0.0:5001 --workers 2 --timeout 600 app:app' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf

# ===== СЛОЙ 6: Приложение (часто меняется - ПОСЛЕДНИЙ!) =====
COPY app.py .
COPY bootstrap.py .
COPY gunicorn_config.py .

EXPOSE 5001

# Запускаем supervisor (Redis + Gunicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
