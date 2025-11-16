# Video Processor API

**Open Source** REST API for video processing with FFmpeg. Create vertical Shorts, add subtitles, cut videos, extract audio.

[![Docker Hub](https://img.shields.io/docker/v/alexbic/video-processor-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/alexbic/video-processor-api)
[![GitHub](https://img.shields.io/badge/GitHub-alexbic/video--processor--api-blue?logo=github)](https://github.com/alexbic/video-processor-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](RELEASE_NOTES_v1.1.0.md)

**English** | [Русский](README.ru.md)

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
- 🛡️ **Input Validation** - автоматическая проверка медиа-файлов перед обработкой
- 🔗 **Full URLs** - абсолютные ссылки во всех ответах для n8n/внешних интеграций

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

### 🔐 Authentication

API supports **smart dual-mode operation** with Bearer token authentication:

**🔑 Two Operation Modes:**

1️⃣ **Public API Mode** (when `API_KEY` is set):
   - Protected endpoints require Bearer token authentication
   - `PUBLIC_BASE_URL` should be configured for external access
   - Download URLs use public domain from `PUBLIC_BASE_URL`
   - Recommended for production with reverse proxy/CDN

2️⃣ **Internal Docker Network Mode** (when `API_KEY` is NOT set):
   - All endpoints work without authentication
   - API operates within Docker network (e.g., with n8n)
   - `PUBLIC_BASE_URL` is **ignored** (even if set)
   - Download URLs use internal Docker hostnames (`http://video-processor:5001`)
   - Ideal for trusted internal services

**Setup:**
```bash
# Generate secure API key
openssl rand -hex 32

# Public API mode (requires authentication)
export API_KEY="your-generated-key-here"
export PUBLIC_BASE_URL="https://your-domain.com/video-api"

# Internal Docker mode (no authentication)
# Don't set API_KEY - PUBLIC_BASE_URL will be ignored
unset API_KEY
```

**Usage with API Key:**
```bash
curl -H "Authorization: Bearer your-api-key" \
  -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "...", "operations": [...]}'
```

**Endpoint Protection:**
- ✅ **Always public**: `/health`, `/task_status/{task_id}`, `/download/{task_id}/...`
- 🔒 **Protected when API_KEY set**: `/process_video`, `/tasks`, `/fonts`
- 🔐 **Task access**: `task_id` acts as temporary access token (UUID, 2h TTL)

---

### Client Metadata (Pass-through)

Добавьте в запрос поле `client_meta` (любой JSON-объект), и он будет:
- сохранён в `metadata.json` задачи,
- включён в ответы `/process_video` (sync), `/task_status/{task_id}` (async),
- отправлен в payload вебхуков (`task_completed`/`task_failed`).

Это удобно для заголовков/подписей под разные соцсети, ID кампании, trace-id и т.д.

Пример запроса c `client_meta`:
```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [{"type": "make_short", "crop_mode": "letterbox"}],
  "client_meta": {
    "titles": {
      "tiktok": "Крутой ролик про AI",
      "youtube": "Amazing AI Demo",
      "instagram": "AI в действии"
    },
    "campaign_id": "cmp-2025-11-13"
  }
}
```
В ответах поле будет доступно как `client_meta` без изменений.

Limits (to protect the service):
- Max size: `16 KB` (UTF‑8 JSON)
- Max depth: `5` levels
- Max total keys: `200`
- Max list length: `200`
- Max string length: `1000` chars
- Allowed types: objects, arrays, strings, numbers, booleans, null

Compatibility: `client_meta` may also be sent as a JSON string (it will be parsed server-side). Prefer sending an object directly.

n8n tip: if you have a nested object available only via string, you can send it using `toJsonString()` and the API will parse nested JSON strings too. Example:
```json
{
  "client_meta": {
    "metadata": {{ $json.metadata.toJsonString() }}
  }
}
```
The server will convert `metadata` from a JSON string to an object before validation and saving.

Immediate echo:
- Sync mode: `client_meta` is included in the final response.
- Async mode: `client_meta` is included immediately in the 202 response (along with `task_id` and `check_status_url`).

---

### Endpoints Overview

- `GET /health` — состояние сервиса (версии, `storage_mode`, доступность Redis) **[без авторизации]**
- `GET /fonts` — список системных и кастомных шрифтов **[требует API key]**
- `POST /process_video` — запуск pipeline (sync/async; `operations`, опционально `webhook_url`) **[требует API key]**
- `GET /task_status/{task_id}` — статус задачи (`queued`/`processing`/`completed`/`error`) **[без авторизации]**
- `GET /tasks` — последние задачи (для отладки) **[требует API key]**
- `GET /download/{task_id}/{filename}` — скачать готовый файл **[без авторизации]**
- `GET /download/{task_id}/metadata.json` — метаданные результата **[без авторизации]**

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
  "api_key_enabled": true,
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
        "type": "make_short",
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
- `to_shorts` - конверсия в Shorts формат (letterbox + title + subtitles); поддерживает `start_time`/`end_time` для автоматической нарезки
- `extract_audio` - извлечение аудиодорожки

---

### Response Format (Формат ответа)

**Унифицированный формат** - все операции возвращают одинаковую структуру:

```json
{
  "task_id": "abc123",
  "status": "completed",
  "video_url": "https://example.com/video.mp4",
  "output_files": [
    {
      "filename": "output.mp4",
      "file_size": 16040960,
      "file_size_mb": 15.3,
      "download_url": "http://video-processor:5001/download/abc123/output.mp4",
      "download_path": "/download/abc123/output.mp4"
    }
  ],
  "total_files": 1,
  "is_chunked": false,
  "metadata_url": "/download/abc123/metadata.json",
  "completed_at": "2025-01-08T10:05:23"
}
```

**Ключевые поля:**
- `video_url` - исходный URL видео, с которым работали
- `output_files` - **всегда массив** (даже если 1 файл)
- `is_chunked` - `true` если файлы разбиты на чанки (для Whisper API)
- `total_files` - общее количество файлов

### Error Responses (Ошибки)

Все ошибки возвращаются с HTTP-кодом, полем `status: "error"` и сообщением в `error`.

- 400 Bad Request (валидация):
  ```json
  { "status": "error", "error": "video_url is required" }
  ```
- 404 Not Found (статус задачи):
  ```json
  { "status": "error", "error": "Task not found" }
  ```
- 403 Forbidden (скачивание файла вне task-директории):
  ```json
  { "status": "error", "error": "Invalid file path" }
  ```
- 404 Not Found (файл не найден при скачивании):
  ```json
  { "status": "error", "error": "File not found" }
  ```
- 500 Internal Server Error (ошибка выполнения):
  ```json
  { "status": "error", "error": "FFmpeg error: ..." }
  ```

В вебхуках при ошибке событие остаётся `event: "task_failed"`, а статус — `status: "error"`.

**Для chunked файлов** (extract_audio с разбиением):
```json
{
  "output_files": [
    {"filename": "audio_chunk_000.mp3", "chunk": "1:7", ...},
    {"filename": "audio_chunk_001.mp3", "chunk": "2:7", ...}
  ],
  "is_chunked": true
}
```

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
  "task_id": "abc123",
  "status": "completed",
  "video_url": "https://example.com/video.mp4",
  "output_files": [
    {
      "filename": "output_20250108_100523.mp4",
      "file_size": 16040960,
      "file_size_mb": 15.3,
      "download_url": "http://video-processor:5001/download/abc123/output_20250108_100523.mp4",
      "download_path": "/download/abc123/output_20250108_100523.mp4"
    }
  ],
  "total_files": 1,
  "is_chunked": false,
  "metadata_url": "/download/abc123/metadata.json",
  "note": "Files will auto-delete after 2 hours.",
  "completed_at": "2025-01-08T10:05:23"
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
  "video_url": "https://example.com/video.mp4",
  "output_files": [
    {
      "filename": "output.mp4",
      "file_size": 16040960,
      "file_size_mb": 15.3,
      "download_url": "http://video-processor:5001/download/abc123/output.mp4",
      "download_path": "/download/abc123/output.mp4"
    }
  ],
  "total_files": 1,
  "total_size": 16040960,
  "is_chunked": false,
  "metadata_url": "http://video-processor:5001/download/abc123/metadata.json",
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
  "video_url": "https://example.com/video.mp4",
  "output_files": [
    {
      "filename": "output.mp4",
      "file_size": 16040960,
      "file_size_mb": 15.3,
      "download_url": "http://video-processor:5001/download/abc123/output.mp4",
      "download_path": "/download/abc123/output.mp4"
    }
  ],
  "total_files": 1,
  "total_size": 16040960,
  "total_size_mb": 15.3,
  "is_chunked": false,
  "metadata_url": "http://video-processor:5001/download/abc123/metadata.json",
  "file_ttl_seconds": 7200,
  "file_ttl_human": "2 hours",
  "operations_executed": 1,
  "completed_at": "2025-01-08T10:05:23"
}
```

**Webhook Payload (error):**
```json
{
  "task_id": "abc123",
  "event": "task_failed",
  "status": "error",
  "error": "FFmpeg error: ...",
  "failed_at": "2025-01-08T10:05:23"
}
```

**Retry логика:**
- 3 попытки отправки
- Exponential backoff: 1s, 2s, 4s

---

### Status Lifecycle

Статусы задач и переходы:

- `queued` → задача создана и поставлена в очередь (async)
- `processing` → выполняются операции (`progress` 5–95%)
- `completed` → готово; доступны `output_files`, `is_chunked`, `metadata_url`, `video_url`
- `error` → ошибка выполнения; `error` — описание, `failed_at` — время

Ключевые поля статуса:
- `task_id`: идентификатор задачи
- `status`: `queued` | `processing` | `completed` | `error`
- `progress`: 0–100 (для async)
- `created_at` / `completed_at` / `failed_at`: временные метки
- `output_files`: всегда массив; при чанкинге содержит `chunk: "i:n"`
- `is_chunked`: `true` если в `output_files` есть поле `chunk`

Рекомендации по поллингу:
- Опрос `GET /task_status/{task_id}` каждые 2–3 секунды
- Останавливать опрос при `status` в {`completed`, `error`}

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
| - | - | - |
| `API_KEY` | — | Enables public mode (Bearer required). When unset, internal mode (no auth). |
| `PUBLIC_BASE_URL` | — | External base for absolute URLs (https://host/app). Used only if `API_KEY` is set. |
| `INTERNAL_BASE_URL` | `http://video-processor:5001` | Base for background URL generation (webhooks, logs). |
| `WORKERS` | `1` | Gunicorn workers. Use `>=2` only with Redis. |
| `REDIS_HOST` | `redis` | Redis host for multi-worker task store. |
| `REDIS_PORT` | `6379` | Redis port. |
| `REDIS_DB` | `0` | Redis DB index. |
| `RECOVERY_ENABLED` | `true` | Auto recovery scan at startup (and optionally periodic). |
| `RECOVERY_INTERVAL_MINUTES` | `0` | Periodic recovery scan interval. `0` = only on startup. |
| `MAX_TASK_RETRIES` | `3` | Max retries for stuck tasks before failing. |
| `RETRY_DELAY_SECONDS` | `60` | Delay between recovery retries. |
| `TASK_TTL_HOURS` | `2` | TTL for task files in /app/tasks. |
| `RECOVERY_PUBLIC_ENABLED` | `false` | Enable public manual recovery endpoint `/recover/{task_id}`. |
| `ALLOW_NESTED_JSON_IN_META` | `true` | Try to parse nested JSON strings in `client_meta`. |
| `MAX_CLIENT_META_BYTES` | `16384` | Size limit for `client_meta` (bytes). |
| `MAX_CLIENT_META_DEPTH` | `5` | Max nesting for `client_meta`. |
| `MAX_CLIENT_META_KEYS` | `200` | Max keys in `client_meta` object. |
| `MAX_CLIENT_META_STRING_LENGTH` | `1000` | Max length of string values. |
| `MAX_CLIENT_META_LIST_LENGTH` | `200` | Max list length. |

Notes:
- With `API_KEY` set + `PUBLIC_BASE_URL` defined → service exposes absolute URLs and requires Bearer token.
- Without `API_KEY` → internal mode suitable for Docker network usage (no auth).
- `check_status_url` is always absolute in async responses.

### Manual Recovery (optional)

- Endpoint: `GET/POST /recover/{task_id}`
- Enable via `RECOVERY_PUBLIC_ENABLED=true` (use only in trusted network)
- Optional query: `force=1` to ignore expired TTL

Response:
```json
{ "task_id": "...", "ok": true, "message": "Recovery started", "status": "processing", "retry_count": 1 }
```

## 📖 Examples

### Example 1: Shorts с автоматической нарезкой (start_time/end_time)

```json
{
  "video_url": "https://example.com/long-video.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "make_short",
      "start_time": 10.5,
      "end_time": 70.0,
      "crop_mode": "letterbox",
      "title": {
        "text": "Мой первый Shorts",
        "font": "DejaVu Sans Bold",
        "fontsize": 70,
        "fontcolor": "white"
      },
      "subtitles": {
        "items": [
          {"text": "Первый субтитр", "start": 0, "end": 3}
        ],
        "font": "Roboto",
        "fontsize": 64,
        "fontcolor": "yellow"
      }
    }
  ]
}
```

**Примечание:** `start_time` и `end_time` могут быть числами (секунды) или строками (`"00:01:30"`). При указании обоих параметров будет вырезан фрагмент автоматически.

**Формат полей:**
- `title` — объект с полем `text` и настройками шрифта
- `subtitles` — объект с полем `items` (массив субтитров) и настройками шрифта

### Example 2: Простая конверсия в Shorts (без нарезки)

```json
{
  "video_url": "https://example.com/landscape.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "make_short",
      "letterbox_config": {
        "width": 1080,
        "height": 1920,
        "color": "black"
      }
    }
  ]
}
```

### Example 3: Shorts с заголовком и субтитрами

```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "make_short",
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

### Example 4: Нарезка видео

```json
{
  "video_url": "https://example.com/long-video.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "cut_video",
      "start_time": "00:01:30",
      "end_time": "00:02:00"
    }
  ]
}
```

### Example 5: Pipeline - несколько операций

```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "cut_video",
      "start_time": "00:00:10",
      "end_time": "00:01:00"
    },
    {
      "type": "make_short",
      "letterbox_config": {"width": 1080, "height": 1920},
      "title": {"text": "Episode 1", "fontsize": 70}
    }
  ]
}
```

### Example 6: Извлечение аудио (sync режим)

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
  "task_id": "abc123-def456",
  "status": "completed",
  "output_files": [
    {
      "filename": "audio_20251112_194523.mp3",
      "file_size": 5048576,
      "file_size_mb": 4.8,
      "download_url": "http://localhost:5001/download/abc123-def456/audio_20251112_194523.mp3",
      "download_path": "/download/abc123-def456/audio_20251112_194523.mp3"
    }
  ],
  "total_files": 1,
  "is_chunked": false,
  "metadata_url": "http://localhost:5001/download/abc123-def456/metadata.json",
  "note": "Files will auto-delete after 2 hours.",
  "completed_at": "2025-11-12T19:45:23"
}
```

### Example 7: Извлечение аудио (async режим с webhook)

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
  "task_id": "abc123-def456",
  "status": "processing",
  "message": "Task created and processing in background",
  "check_status_url": "http://video-processor:5001/task_status/abc123-def456"
}
```

**Note (v1.1.0):** `check_status_url` теперь всегда полный URL (включая схему и хост), готовый для использования в n8n и других системах.

**Проверка статуса задачи:**
```bash
curl http://localhost:5001/task_status/abc123-def456
```

**Response (когда готово):**
```json
{
  "task_id": "abc123-def456",
  "status": "completed",
  "progress": 100,
  "output_files": [
    {
      "filename": "audio_20251112_194523.mp3",
      "file_size": 5048576,
      "file_size_mb": 4.8,
      "download_url": "http://video-processor:5001/download/abc123-def456/audio_20251112_194523.mp3",
      "download_path": "/download/abc123-def456/audio_20251112_194523.mp3"
    }
  ],
  "total_files": 1,
  "total_size": 5048576,
  "is_chunked": false,
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
      "download_url": "http://video-processor:5001/download/abc123-def456/audio_20251112_194523.mp3",
      "download_path": "/download/abc123-def456/audio_20251112_194523.mp3"
    }
  ],
  "total_files": 1,
  "total_size": 5048576,
  "total_size_mb": 4.8,
  "is_chunked": false,
  "metadata_url": "http://video-processor:5001/download/abc123-def456/metadata.json",
  "file_ttl_seconds": 7200,
  "file_ttl_human": "2 hours",
  "operations_executed": 1,
  "completed_at": "2025-11-12T19:45:23"
}
```

### Example 8: Нарезка видео + извлечение аудио (pipeline)

```json
{
  "video_url": "https://example.com/long-video.mp4",
  "execution": "async",
  "operations": [
    {
      "type": "cut_video",
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

Примечание: При включённом разбиении (через `chunk_duration_minutes` или `max_chunk_size_mb`) каждый объект в `output_files` дополнительно содержит только одно поле:
- `chunk`: компактный индекс чанка в формате `i:n` (например, `"1:7"`)

### Example 9: Извлечение аудио с автоматическим chunking для Whisper API

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
      "download_url": "http://video-processor:5001/download/xyz123/audio_20251112_194523_chunk000.mp3",
      "download_path": "/download/xyz123/audio_20251112_194523_chunk000.mp3"
    },
    {
      "filename": "audio_20251112_194523_chunk001.mp3",
      "file_size": 24330240,
      "file_size_mb": 23.2,
      "chunk": "2:3",
      "download_url": "http://video-processor:5001/download/xyz123/audio_20251112_194523_chunk001.mp3",
      "download_path": "/download/xyz123/audio_20251112_194523_chunk001.mp3"
    },
    {
      "filename": "audio_20251112_194523_chunk002.mp3",
      "file_size": 18980864,
      "file_size_mb": 18.1,
      "chunk": "3:3",
      "download_url": "http://video-processor:5001/download/xyz123/audio_20251112_194523_chunk002.mp3",
      "download_path": "/download/xyz123/audio_20251112_194523_chunk002.mp3"
    }
  ],
  "total_files": 3,
  "total_size": 67952640,
  "total_size_mb": 64.8,
  "is_chunked": true,
  "metadata_url": "http://video-processor:5001/download/xyz123/metadata.json",
  "file_ttl_seconds": 7200,
  "file_ttl_human": "2 hours",
  "operations_executed": 1,
  "completed_at": "2025-11-12T19:45:23"
}
```

**Файлы доступны по следующим URL:**
```
/download/xyz123/audio_20251112_194523_chunk000.mp3  (23.5 MB, 0:00 - 15:30)
/download/xyz123/audio_20251112_194523_chunk001.mp3  (23.2 MB, 15:30 - 31:00)
/download/xyz123/audio_20251112_194523_chunk002.mp3  (18.1 MB, 31:00 - 45:00)
/download/xyz123/metadata.json  (метаданные всех файлов)
```

**Как скачать все чанки:**
```bash
# Все чанки доступны по паттерну
curl http://localhost:5001/download/xyz123/audio_20251112_194523_chunk000.mp3 -o chunk000.mp3
curl http://localhost:5001/download/xyz123/audio_20251112_194523_chunk001.mp3 -o chunk001.mp3
curl http://localhost:5001/download/xyz123/audio_20251112_194523_chunk002.mp3 -o chunk002.mp3
```

**Поля чанков в ответах:**
- `chunk`: индекс текущего чанка и общее число в формате `i:n`

### Example 10: Ручное задание длительности чанков

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
  "task_id": "def456-ghi789",
  "output_files": [
    {
      "filename": "audio_20251112_200100_chunk000.mp3",
      "file_size": 24117248,
      "file_size_mb": 23.0,
      "chunk": "1:6",
      "download_url": "http://localhost:5001/download/def456-ghi789/audio_20251112_200100_chunk000.mp3",
      "download_path": "/download/def456-ghi789/audio_20251112_200100_chunk000.mp3"
    },
    {
      "filename": "audio_20251112_200100_chunk001.mp3",
      "file_size": 24379392,
      "file_size_mb": 23.25,
      "chunk": "2:6",
      "download_url": "http://localhost:5001/download/def456-ghi789/audio_20251112_200100_chunk001.mp3",
      "download_path": "/download/def456-ghi789/audio_20251112_200100_chunk001.mp3"
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
| `API_KEY` | `None` | Bearer token for authentication. If set, enables Public API mode with protected endpoints. If not set, runs in Internal mode without authentication. |
| `PUBLIC_BASE_URL` | `None` | External base URL for download links (e.g., `https://domain.com/api`). Only used when `API_KEY` is set. Ignored in Internal mode. |
| `INTERNAL_BASE_URL` | `http://video-processor:5001` | Internal Docker network URL for background tasks. Used when generating URLs in webhooks/metadata without request context. **New in v1.1.0** |
| `WORKERS` | `1` | Number of gunicorn workers (use 2+ with Redis for multi-worker mode) |
| `REDIS_HOST` | `redis` | Redis hostname for multi-worker task storage |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database number |

### Docker Volumes

```yaml
volumes:
  - /path/to/tasks:/app/tasks          # Task-based storage (files + metadata.json)
  - /path/to/fonts:/app/fonts/custom   # Кастомные шрифты
```

**Структура task-директории:**
```
/app/tasks/{task_id}/
  ├── input_*.mp4       # Входные файлы (удаляются после обработки)
  ├── temp_*.mp4        # Промежуточные файлы (удаляются после обработки)
  ├── short_*.mp4       # Готовые Shorts видео (TTL: 2 часа)
  ├── video_*.mp4       # Готовые нарезанные видео (TTL: 2 часа)
  ├── audio_*.mp3       # Извлечённые аудиодорожки (TTL: 2 часа)
  └── metadata.json    # Метаданные всех файлов
```

---

## 📝 File Retention

- **Task directories**: Автоматически удаляются через **2 часа** после создания
- **Input/Temp files**: Файлы с префиксами `input_*` и `temp_*` удаляются сразу после завершения обработки
- **Output files**: Файлы с префиксами `short_*`, `video_*`, `audio_*` хранятся 2 часа в `/app/tasks/{task_id}/`
- **Redis Tasks**: TTL = 24 часа
- **Metadata.json**: Хранится 2 часа и используется как fallback для `/task_status` когда задачи нет в Redis/memory **(v1.1.0)**

---

## 🛠 Development

## 💡 Client Integration Tips

- `output_files`: всегда массив. Даже при одном файле используйте итерацию.
- `is_chunked`: определяйте пакетную обработку по этому флагу и/или наличию `chunk`.
- `chunk` формат: строка `"i:n"`, где `i` — 1-базовый индекс, `n` — общее число частей.
- `client_meta`: передайте произвольный JSON в запросе — он вернётся как есть в ответах, вебхуке и `metadata.json`.
- Ссылки скачивания: используйте `download_url` для публичного доступа и `download_path` для внутренних вызовов через API-шлюз.
- Метаданные: `metadata_url` содержит полный снимок результата — удобно для кэширования.
- Вебхуки: обрабатывайте оба события — `task_completed` и `task_failed`.
- TTL: файлы хранятся 2 часа; скачайте/переложите в постоянное хранилище сразу после `completed`.
- **Входные URL** **(v1.1.0)**: Передавайте прямые ссылки на медиа-файлы, не на HTML-страницы. API автоматически проверяет Content-Type и отклоняет некорректные файлы с понятными ошибками.
- **Полные URL** **(v1.1.0)**: Все URL в ответах (`check_status_url`, `download_url`, `metadata_url`) теперь абсолютные, готовые для использования в n8n и внешних системах.
- **404 защита** **(v1.1.0)**: Endpoint `/task_status` использует filesystem fallback — даже если задача отсутствует в Redis/memory, статус будет прочитан из `metadata.json`.

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
  -d '{"video_url": "https://example.com/video.mp4", "mode": "simple", "operations": [{"type": "make_short"}]}'
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

