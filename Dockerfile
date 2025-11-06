FROM python:3.11-slim

# Установка FFmpeg и необходимых зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .

# Создание директорий для загрузок и выходных файлов
RUN mkdir -p /app/uploads /app/outputs && \
    chmod 755 /app/uploads /app/outputs

# Открытие порта
EXPOSE 5001

# Запуск приложения через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "2", "--timeout", "600", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
