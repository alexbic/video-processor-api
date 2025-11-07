FROM python:3.11-slim

# Установка FFmpeg, шрифтов и необходимых зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-liberation2 \
    fonts-noto-core \
    fonts-noto-ui-core \
    fonts-roboto \
    fonts-open-sans \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .

# Создание директорий для загрузок, выходных файлов и кастомных шрифтов
RUN mkdir -p /app/uploads /app/outputs /app/fonts/custom && \
    chmod 755 /app/uploads /app/outputs /app/fonts /app/fonts/custom

# Открытие порта
EXPOSE 5001

# Environment variables (can be overridden in docker-compose)
ENV WORKERS=1 \
    REDIS_HOST=redis \
    REDIS_PORT=6379 \
    REDIS_DB=0

# Запуск приложения через gunicorn
# WORKERS=1 by default (safe without Redis)
# Set WORKERS=2+ and configure REDIS_HOST for multi-worker mode
CMD gunicorn --bind 0.0.0.0:5001 --workers ${WORKERS} --timeout 600 --access-logfile - --error-logfile - app:app
