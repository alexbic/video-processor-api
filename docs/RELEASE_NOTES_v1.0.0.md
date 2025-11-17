## 🎉 Video Processor API v1.0.0

Первый официальный релиз открытого REST API для обработки видео (FFmpeg) с поддержкой Shorts, субтитров, нарезки, извлечения аудио и вебхуков.

### ✨ Основные возможности
- Pipeline над видео (набор операций)
- Letterbox / конверсия в вертикальный формат (1080x1920)
- Динамические субтитры и текстовые оверлеи
- Нарезка видео по таймкодам
- Извлечение аудио (mp3/aac) + авточанкинг для Whisper API
- Webhooks с retry (task_completed / task_failed)
- Async / Sync режимы выполнения
- Custom fonts (.ttf/.otf)
- Redis multi-worker режим

### 🔧 API Modes
- Public API (с `API_KEY`) – защищённые эндпоинты + публичные download URL
- Internal Docker Mode (без `API_KEY`) – упрощённый доступ в доверенной сети

### 🚀 Быстрый старт
```bash
docker pull alexbic/video-processor-api:latest
docker run -d -p 5001:5001 \
  -v $(pwd)/tasks:/app/tasks \
  --name video-processor \
  alexbic/video-processor-api:latest
```

### 🐳 Docker Compose (Redis multi-worker)
См. `docker-compose.redis-example.yml`.

### 📚 Документация
- README.md / README.ru.md – общие сведения и примеры
- FONTS.md – кастомные шрифты

### ✅ Эндпоинты (ключевые)
- `POST /process_video` – запуск операций
- `GET /task_status/{task_id}` – статус задачи
- `GET /download/{task_id}/output/{file}` – выдача результата
- `GET /fonts` – список шрифтов
- `GET /health` – состояние сервиса

### 🕒 TTL Файлов
Output файлы живут 2 часа, затем очищаются.

### 🧪 Пример операции (Shorts + субтитры)
```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "to_shorts",
      "letterbox_config": {"width": 1080, "height": 1920},
      "title": {"text": "My Shorts", "font": "DejaVu Sans Bold", "fontsize": 70},
      "subtitles": {"items": [{"text": "Hello", "start": 0, "end": 2}]}
    }
  ]
}
```

### 🔄 Webhook Payload (успех)
```json
{
  "task_id": "abc123",
  "event": "task_completed",
  "status": "completed",
  "output_files": [{"filename": "output.mp4", "download_url": "..."}]
}
```

### 🤝 Contributions
PR приветствуются. Открывайте issue перед крупными изменениями.

— Спасибо за использование Video Processor API! 🚀
