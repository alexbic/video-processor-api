# Video Processor API

**Open Source** REST API для обработки видео с FFmpeg. Создание вертикальных Shorts, субтитры, нарезка, извлечение аудио.

[![Docker Hub](https://img.shields.io/docker/v/alexbic/video-processor-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/alexbic/video-processor-api)
[![GitHub](https://img.shields.io/badge/GitHub-alexbic/video--processor--api-blue?logo=github)](https://github.com/alexbic/video-processor-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

- 🎬 **Pipeline Processing** - цепочка операций над видео (letterbox → title → subtitles)
- 📦 **Letterbox Mode** - горизонтальное видео в вертикальный формат (1080x1920) с размытым фоном
- 📝 **Динамические субтитры** - с поддержкой кастомных шрифтов, цветов, позиций
- 🎨 **Текстовые оверлеи** - заголовки с fade-эффектами
- ✂️ **Нарезка видео** - по таймкодам с конвертацией в Shorts
- 🎵 **Извлечение аудио** - из видеофайлов
- 📡 **Webhooks** - уведомления о завершении обработки с retry-логикой
- ⚡ **Async Processing** - фоновая обработка с отслеживанием статуса
- 🔠 **Custom Fonts** - поддержка загрузки своих шрифтов (.ttf/.otf)
- 🐳 **Redis Support** - multi-worker режим для высоких нагрузок

---

## 🚀 Quick Start

### Single Worker (без Redis)

```bash
docker pull alexbic/video-processor-api:latest
docker run -d -p 5001:5001 \
  -v $(pwd)/tasks:/app/tasks \
  --name video-processor \
  alexbic/video-processor-api:latest
```

### Multi-Worker с Redis (рекомендуется для production)

См. [docker-compose.redis-example.yml](docker-compose.redis-example.yml) для полной конфигурации.

```bash
docker-compose up -d redis video-processor
```

API автоматически определяет доступность Redis:
- **С Redis**: Multi-worker mode (2+ workers)
- **Без Redis**: Single-worker mode (fallback)

---

## 📚 API Reference

### Health Check

```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "video-processor-api",
  "storage_mode": "redis",
  "redis_available": true,
  "timestamp": "2025-01-08T10:00:00"
}
```

---

### Доступные шрифты

```bash
curl http://localhost:5001/fonts
```

**Response:**
```json
{
  "status": "success",
  "total_fonts": 10,
  "fonts": {
    "system_fonts": [
      {"name": "DejaVu Sans", "family": "sans-serif"},
      {"name": "DejaVu Sans Bold", "family": "sans-serif"},
      {"name": "Roboto", "family": "sans-serif"},
      ...
    ],
    "custom_fonts": []
  }
}
```

**Кастомные шрифты:**
1. Поместите .ttf/.otf файлы в `/opt/n8n-docker/volumes/video_processor/fonts/`
2. Перезапустите контейнер
3. Используйте через `"font": "YourFontName"`

См. [FONTS.md](FONTS.md) для подробностей.

---

### Обработка видео

`POST /process_video`

Используйте готовые операции для обработки видео:

```bash
curl -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "execution": "sync",
    "operations": [
      {
        "type": "to_shorts",
        "letterbox_config": {
          "width": 1080,
          "height": 1920,
          "color": "black"
        },
        "title": {
          "text": "My Shorts Video",
          "font": "DejaVu Sans Bold",
          "fontsize": 70,
          "fontcolor": "white",
          "x": "center",
          "y": 100
        },
        "subtitles": {
          "items": [
            {"text": "First subtitle", "start": 0, "end": 3},
            {"text": "Second subtitle", "start": 3, "end": 6}
          ],
          "font": "Roboto",
          "fontsize": 64,
          "fontcolor": "yellow"
        }
      }
    ],
    "webhook_url": "https://n8n.example.com/webhook/video-completed"
  }'
```

**Доступные операции:**
- `cut` - нарезка видео по таймкодам
- `to_shorts` - конверсия в Shorts формат (letterbox + title + subtitles)
- `extract_audio` - извлечение аудиодорожки

---

### Execution Modes

#### Sync (синхронный)

```json
{
  "execution": "sync"
}
```

**Response (сразу):**
```json
{
  "success": true,
  "filename": "output_20250108_100523.mp4",
  "file_size_mb": 15.3,
  "download_url": "http://video-processor:5001/download/output_20250108_100523.mp4",
  "note": "File will auto-delete after 2 hours."
}
```

#### Async (асинхронный)

```json
{
  "execution": "async"
}
```

**Response (сразу):**
```json
{
  "success": true,
  "task_id": "abc123",
  "status": "processing",
  "message": "Task created and processing in background"
}
```

**Проверка статуса:**
```bash
curl http://localhost:5001/task_status/abc123
```

**Response:**
```json
{
  "task_id": "abc123",
  "status": "completed",
  "progress": 100,
  "filename": "output.mp4",
  "download_url": "http://video-processor:5001/download/output.mp4",
  "completed_at": "2025-01-08T10:05:23"
}
```

---

### Webhooks

Добавьте `webhook_url` для получения уведомлений:

```json
{
  "webhook_url": "https://n8n.example.com/webhook/video-completed"
}
```

**Webhook Payload (success):**
```json
{
  "task_id": "abc123",
  "event": "task_completed",
  "status": "completed",
  "filename": "output.mp4",
  "file_size_mb": 15.3,
  "file_ttl_seconds": 7200,
  "file_ttl_human": "2 hours",
  "download_url": "http://video-processor:5001/download/output.mp4",
  "completed_at": "2025-01-08T10:05:23"
}
```

**Webhook Payload (error):**
```json
{
  "task_id": "abc123",
  "event": "task_failed",
  "status": "failed",
  "error": "FFmpeg error: ...",
  "failed_at": "2025-01-08T10:05:23"
}
```

**Retry логика:**
- 3 попытки отправки
- Exponential backoff: 1s, 2s, 4s

---

## 📖 Examples

### Example 1: Простая конверсия в Shorts

```json
{
  "video_url": "https://example.com/landscape.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "to_shorts",
      "letterbox_config": {
        "width": 1080,
        "height": 1920,
        "color": "black"
      }
    }
  ]
}
```

### Example 2: Shorts с заголовком и субтитрами

```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "to_shorts",
      "letterbox_config": {"width": 1080, "height": 1920, "color": "#1a1a1a"},
      "title": {
        "text": "Amazing Content",
        "font": "DejaVu Sans Bold",
        "fontsize": 80,
        "fontcolor": "yellow",
        "box": true,
        "boxcolor": "black@0.5"
      },
      "subtitles": {
        "items": [
          {"text": "Welcome to our channel", "start": 0, "end": 3},
          {"text": "Subscribe for more", "start": 3, "end": 6}
        ],
        "font": "Roboto",
        "fontsize": 64,
        "fontcolor": "white"
      }
    }
  ],
  "webhook_url": "https://n8n.example.com/webhook/completed"
}
```

### Example 3: Нарезка видео

```json
{
  "video_url": "https://example.com/long-video.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "cut",
      "start_time": "00:01:30",
      "end_time": "00:02:00"
    }
  ]
}
```

### Example 4: Pipeline - несколько операций

```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "cut",
      "start_time": "00:00:10",
      "end_time": "00:01:00"
    },
    {
      "type": "to_shorts",
      "letterbox_config": {"width": 1080, "height": 1920},
      "title": {"text": "Episode 1", "fontsize": 70}
    }
  ]
}
```

### Example 5: Извлечение аудио (sync режим)

```bash
curl -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "execution": "sync",
    "operations": [
      {
        "type": "extract_audio",
        "format": "mp3",
        "bitrate": "192k"
      }
    ]
  }'
```

**Response (sync - возвращается сразу после завершения):**
```json
{
  "success": true,
  "task_id": "abc123-def456",
  "output_files": [
    {
      "filename": "audio_20251112_194523.mp3",
      "file_size": 5048576,
      "file_size_mb": 4.8,
      "download_url": "http://localhost:5001/download/abc123-def456/output/audio_20251112_194523.mp3",
      "download_path": "/download/abc123-def456/output/audio_20251112_194523.mp3"
    }
  ],
  "total_files": 1,
  "metadata_url": "http://localhost:5001/download/abc123-def456/metadata.json",
  "operations_executed": 1,
  "note": "Files will auto-delete after 2 hours.",
  "completed_at": "2025-11-12T19:45:23"
}
```

### Example 6: Извлечение аудио (async режим с webhook)

```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "extract_audio",
      "format": "mp3",
      "bitrate": "320k"
    }
  ],
  "webhook_url": "https://n8n.example.com/webhook/audio-ready"
}
```

**Response (async - возвращается сразу):**
```json
{
  "success": true,
  "task_id": "abc123-def456",
  "status": "processing",
  "message": "Task created and processing in background",
  "check_status_url": "/task_status/abc123-def456"
}
```

**Проверка статуса задачи:**
```bash
curl http://localhost:5001/task_status/abc123-def456
```

**Response (когда готово):**
```json
{
  "success": true,
  "task_id": "abc123-def456",
  "status": "completed",
  "progress": 100,
  "output_files": [
    {
      "filename": "audio_20251112_194523.mp3",
      "file_size": 5048576,
      "file_size_mb": 4.8,
      "download_url": "http://video-processor:5001/download/abc123-def456/output/audio_20251112_194523.mp3",
      "download_path": "/download/abc123-def456/output/audio_20251112_194523.mp3"
    }
  ],
  "total_files": 1,
  "metadata_url": "http://video-processor:5001/download/abc123-def456/metadata.json",
  "completed_at": "2025-11-12T19:45:23"
}
```

**Webhook payload (отправляется автоматически при завершении):**
```json
{
  "task_id": "abc123-def456",
  "event": "task_completed",
  "status": "completed",
  "output_files": [
    {
      "filename": "audio_20251112_194523.mp3",
      "file_size": 5048576,
      "file_size_mb": 4.8,
      "download_url": "http://video-processor:5001/download/abc123-def456/output/audio_20251112_194523.mp3",
      "download_path": "/download/abc123-def456/output/audio_20251112_194523.mp3"
    }
  ],
  "total_files": 1,
  "total_size": 5048576,
  "total_size_mb": 4.8,
  "metadata_url": "http://video-processor:5001/download/abc123-def456/metadata.json",
  "file_ttl_seconds": 7200,
  "file_ttl_human": "2 hours",
  "operations_executed": 1,
  "completed_at": "2025-11-12T19:45:23"
}
```

### Example 7: Нарезка видео + извлечение аудио (pipeline)

```json
{
  "video_url": "https://example.com/long-video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "cut",
      "start_time": "00:01:30",
      "end_time": "00:02:30"
    },
    {
      "type": "extract_audio",
      "format": "mp3",
      "bitrate": "192k"
    }
  ],
  "webhook_url": "https://n8n.example.com/webhook/audio-extracted"
}
```

**Поддерживаемые форматы аудио:**
- `mp3` (codec: libmp3lame) - универсальный формат
- `aac` (codec: aac) - для Apple устройств

**Параметры extract_audio:**
- `format` (опционально): `mp3` (default) или `aac`
- `bitrate` (опционально): `128k`, `192k` (default), `256k`, `320k`
- `chunk_duration_minutes` (опционально): Длительность чанка в минутах для разбиения больших файлов
- `max_chunk_size_mb` (опционально): Максимальный размер чанка в МБ (default: 24 для Whisper API)
- `optimize_for_whisper` (опционально): `true` - оптимизация для Whisper API (16kHz, mono, 64k bitrate)

Примечание: При включённом разбиении (через `chunk_duration_minutes` или `max_chunk_size_mb`) каждый объект в `output_files` дополнительно содержит:
- `chunk`: компактный индекс чанка в формате `i:n` (например, `"1:7"`)

Совместимость: Для обратной совместимости также могут присутствовать поля `chunk_index`, `chunk_total`, `chunk_label` — их можно игнорировать, если вы используете `chunk`.

### Example 8: Извлечение аудио с автоматическим chunking для Whisper API

**Проблема:** Whisper API не принимает файлы больше 25 МБ.

**Решение:** Автоматическое разбиение на чанки < 24 МБ.

```json
{
  "video_url": "https://example.com/long-video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "extract_audio",
      "format": "mp3",
      "max_chunk_size_mb": 24,
      "optimize_for_whisper": true
    }
  ],
  "webhook_url": "https://n8n.example.com/webhook/audio-chunks-ready"
}
```

**Response (async):**
```json
{
  "success": true,
  "task_id": "xyz123",
  "status": "processing",
  "check_status_url": "/task_status/xyz123"
}
```

**Webhook payload (когда готово):**
```json
{
  "task_id": "xyz123",
  "event": "task_completed",
  "status": "completed",
  "output_files": [
    {
      "filename": "audio_20251112_194523_chunk000.mp3",
      "file_size": 24641536,
      "file_size_mb": 23.5,
      "chunk": "1:3",
      "chunk_index": 1,
      "chunk_total": 3,
      "chunk_label": "1/3",
      "download_url": "http://video-processor:5001/download/xyz123/output/audio_20251112_194523_chunk000.mp3",
      "download_path": "/download/xyz123/output/audio_20251112_194523_chunk000.mp3"
    },
    {
      "filename": "audio_20251112_194523_chunk001.mp3",
      "file_size": 24330240,
      "file_size_mb": 23.2,
      "chunk": "2:3",
      "chunk_index": 2,
      "chunk_total": 3,
      "chunk_label": "2/3",
      "download_url": "http://video-processor:5001/download/xyz123/output/audio_20251112_194523_chunk001.mp3",
      "download_path": "/download/xyz123/output/audio_20251112_194523_chunk001.mp3"
    },
    {
      "filename": "audio_20251112_194523_chunk002.mp3",
      "file_size": 18980864,
      "file_size_mb": 18.1,
      "chunk": "3:3",
      "chunk_index": 3,
      "chunk_total": 3,
      "chunk_label": "3/3",
      "download_url": "http://video-processor:5001/download/xyz123/output/audio_20251112_194523_chunk002.mp3",
      "download_path": "/download/xyz123/output/audio_20251112_194523_chunk002.mp3"
    }
  ],
  "total_files": 3,
  "total_size": 67952640,
  "total_size_mb": 64.8,
  "metadata_url": "http://video-processor:5001/download/xyz123/metadata.json",
  "file_ttl_seconds": 7200,
  "file_ttl_human": "2 hours",
  "operations_executed": 1,
  "completed_at": "2025-11-12T19:45:23"
}
```

**Файлы доступны по следующим URL:**
```
/download/xyz123/output/audio_20251112_194523_chunk000.mp3  (23.5 MB, 0:00 - 15:30)
/download/xyz123/output/audio_20251112_194523_chunk001.mp3  (23.2 MB, 15:30 - 31:00)
/download/xyz123/output/audio_20251112_194523_chunk002.mp3  (18.1 MB, 31:00 - 45:00)
/download/xyz123/metadata.json  (метаданные всех файлов)
```

**Как скачать все чанки:**
```bash
# Все чанки доступны по паттерну
curl http://localhost:5001/download/xyz123/output/audio_20251112_194523_chunk000.mp3 -o chunk000.mp3
curl http://localhost:5001/download/xyz123/output/audio_20251112_194523_chunk001.mp3 -o chunk001.mp3
curl http://localhost:5001/download/xyz123/output/audio_20251112_194523_chunk002.mp3 -o chunk002.mp3
```

**Поля чанков в ответах:**
- `chunk_index`: номер текущего чанка (начиная с 1)
- `chunk_total`: сколько чанков всего
- `chunk_label`: человекочитаемая метка `"i/n"`

### Example 9: Ручное задание длительности чанков

```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "extract_audio",
      "format": "mp3",
      "chunk_duration_minutes": 10,
      "optimize_for_whisper": true
    }
  ]
}
```

Создаст чанки по 10 минут каждый, оптимизированные для Whisper API (16kHz, mono, 64k bitrate).

**Response (sync):**
```json
{
  "success": true,
  "task_id": "def456-ghi789",
  "output_files": [
    {
      "filename": "audio_20251112_200100_chunk000.mp3",
      "file_size": 24117248,
      "file_size_mb": 23.0,
      "chunk": "1:6",
      "download_url": "http://localhost:5001/download/def456-ghi789/output/audio_20251112_200100_chunk000.mp3",
      "download_path": "/download/def456-ghi789/output/audio_20251112_200100_chunk000.mp3"
    },
    {
      "filename": "audio_20251112_200100_chunk001.mp3",
      "file_size": 24379392,
      "file_size_mb": 23.25,
      "chunk": "2:6",
      "download_url": "http://localhost:5001/download/def456-ghi789/output/audio_20251112_200100_chunk001.mp3",
      "download_path": "/download/def456-ghi789/output/audio_20251112_200100_chunk001.mp3"
    }
  ],
  "total_files": 6,
  "metadata_url": "http://localhost:5001/download/def456-ghi789/metadata.json",
  "operations_executed": 1,
  "completed_at": "2025-11-12T20:01:25"
}
```

Подсказка: для парсинга `chunk` разделите строку по `:` → `i` и `n`.

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKERS` | `1` | Количество gunicorn workers (используйте 2+ с Redis) |
| `REDIS_HOST` | `redis` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database number |

### Docker Volumes

```yaml
volumes:
  - /path/to/tasks:/app/tasks          # Task-based storage (input/temp/output + metadata.json)
  - /path/to/fonts:/app/fonts/custom   # Кастомные шрифты
```

**Структура task-директории:**
```
/app/tasks/{task_id}/
  ├── input/          # Входные файлы (удаляются после обработки)
  ├── temp/           # Промежуточные файлы (удаляются после обработки)
  ├── output/         # Финальные файлы (TTL: 2 часа)
  └── metadata.json   # Метаданные всех output файлов
```

---

## 📝 File Retention

- **Task directories**: Автоматически удаляются через **2 часа** после создания
- **Input/Temp files**: Удаляются сразу после завершения обработки
- **Output files**: Хранятся 2 часа в `/app/tasks/{task_id}/output/`
- **Redis Tasks**: TTL = 24 часа

---

## 🛠 Development

### Local Build

```bash
git clone https://github.com/alexbic/video-processor-api.git
cd video-processor-api
docker build -t video-processor-api:local .
docker run -d -p 5001:5001 video-processor-api:local
```

### Testing

```bash
# Health check
curl http://localhost:5001/health

# List fonts
curl http://localhost:5001/fonts

# Test simple mode
curl -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4", "mode": "simple", "operations": [{"type": "to_shorts"}]}'
```

---

## 📄 License

MIT License - см. [LICENSE](LICENSE) для подробностей.

---

## 🤝 Contributing

Pull requests приветствуются! Для больших изменений сначала откройте issue.

---

## 📧 Contact

- GitHub: [@alexbic](https://github.com/alexbic)
- Issues: [GitHub Issues](https://github.com/alexbic/video-processor-api/issues)

