# Video Processor API

**Open Source** REST API для обработки видео с FFmpeg. Создание вертикальных Shorts, субтитры, нарезка, извлечение аудио.

[![Docker Hub](https://img.shields.io/docker/v/alexbic/video-processor-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/alexbic/video-processor-api)
[![GitHub](https://img.shields.io/badge/GitHub-alexbic/video--processor--api-blue?logo=github)](https://github.com/alexbic/video-processor-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[English](README.md) | **Русский**

---

## ✨ Возможности

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

## 🚀 Быстрый старт

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

### 🔐 Аутентификация

API поддерживает **умную двухрежимную работу** с Bearer token аутентификацией:

**🔑 Два режима работы:**

1️⃣ **Публичный API режим** (когда `API_KEY` задан):
   - Защищенные endpoints требуют Bearer token аутентификацию
   - `PUBLIC_BASE_URL` должен быть настроен для внешнего доступа
   - Download URL используют публичный домен из `PUBLIC_BASE_URL`
   - Рекомендуется для production с reverse proxy/CDN

2️⃣ **Внутренний Docker режим** (когда `API_KEY` НЕ задан):
   - Все endpoints работают без аутентификации
   - API работает внутри Docker сети (например, с n8n)
   - `PUBLIC_BASE_URL` **игнорируется** (даже если задан)
   - Download URL используют внутренние Docker хосты (`http://video-processor:5001`)
   - Идеально для доверенных внутренних сервисов

**Настройка:**
```bash
# Генерируем безопасный ключ
openssl rand -hex 32

# Публичный API режим (требует аутентификацию)
export API_KEY="your-generated-key-here"
export PUBLIC_BASE_URL="https://your-domain.com/video-api"

# Внутренний Docker режим (без аутентификации)
# Не устанавливаем API_KEY - PUBLIC_BASE_URL будет проигнорирован
unset API_KEY
```

**Использование с API Key:**
```bash
curl -H "Authorization: Bearer your-api-key" \
  -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "...", "operations": [...]}'
```

**Защита endpoints:**
- ✅ **Всегда публичные**: `/health`, `/task_status/{task_id}`, `/download/{task_id}/...`
- 🔒 **Защищены когда API_KEY задан**: `/process_video`, `/tasks`, `/fonts`
- 🔐 **Доступ к задачам**: `task_id` является временным ключом доступа (UUID, TTL 2 часа)

---

### Клиентские метаданные (сквозная передача)

Добавьте поле `client_meta` (любой JSON) в тело запроса. Этот объект будет:
- сохранён в `metadata.json` задачи,
- возвращён в ответах `/process_video` (sync) и `/task_status/{task_id}` (async),
- включён в payload вебхуков (`task_completed`/`task_failed`).

Пример (заголовки для соцсетей + идентификатор кампании):
```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [{"type": "to_shorts"}],
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

Ограничения (для защиты сервиса):
- Максимальный размер: `16 KB` (UTF‑8 JSON)
- Максимальная вложенность: `5` уровней
- Максимум ключей суммарно: `200`
- Максимальная длина списка: `200`
- Максимальная длина строки: `1000` символов
- Разрешённые типы: объекты, массивы, строки, числа, булевы, `null`

Совместимость: `client_meta` можно прислать строкой в формате JSON — сервер попытается распарсить. Предпочтительнее отправлять сразу объект.

Подсказка для n8n: если вложенный объект доступен только как строка, можно отправить через `toJsonString()` — сервер преобразует такую строку обратно в объект. Пример:
```json
{
  "client_meta": {
    "metadata": {{ $json.metadata.toJsonString() }}
  }
}
```
Перед валидацией поле `metadata` будет распознано как объект и сохранено в таком виде.

---

### Обзор Endpoints

- `GET /health` — состояние сервиса (версии, `storage_mode`, доступность Redis) **[без авторизации]**
- `GET /fonts` — список системных и кастомных шрифтов **[требует API key если задан]**
- `POST /process_video` — запуск pipeline (sync/async; `operations`, опционально `webhook_url`) **[требует API key если задан]**
- `GET /task_status/{task_id}` — статус задачи (`queued`/`processing`/`completed`/`error`) **[без авторизации]**
- `GET /tasks` — последние задачи (для отладки) **[требует API key если задан]**
- `GET /download/{task_id}/output/{filename}` — скачать готовый файл **[без авторизации]**
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
      {"name": "Roboto", "family": "sans-serif"}
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
- `to_shorts` - конверсия в Shorts формат (letterbox + title + subtitles); поддерживает `start_time`/`end_time` для автоматической нарезки
- `extract_audio` - извлечение аудиодорожки

---

### Формат ответа

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
      "download_url": "http://video-processor:5001/download/abc123/output/output.mp4",
      "download_path": "/download/abc123/output/output.mp4"
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

### Ошибки

Все ошибки возвращаются с HTTP-кодом, полем `status: "error"` и сообщением в `error`.

- 400 Bad Request (валидация):
  ```json
  { "status": "error", "error": "video_url is required" }
  ```
- 401 Unauthorized (неверный API key):
  ```json
  { "status": "error", "error": "Invalid or missing API key" }
  ```
- 404 Not Found (статус задачи):
  ```json
  { "status": "error", "error": "Task not found" }
  ```
- 403 Forbidden (скачивание файла вне task-директории):
  ```json
  { "status": "error", "error": "Invalid file path" }
  ```
- 500 Internal Server Error (ошибка выполнения):
  ```json
  { "status": "error", "error": "FFmpeg error: ..." }
  ```

---

### Режимы выполнения

#### Sync (синхронный)

```json
{
  "execution": "sync"
}
```

**Response (сразу после завершения):**
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
      "download_url": "http://video-processor:5001/download/abc123/output/output_20250108_100523.mp4",
      "download_path": "/download/abc123/output/output_20250108_100523.mp4"
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
      "download_url": "http://video-processor:5001/download/abc123/output/output.mp4",
      "download_path": "/download/abc123/output/output.mp4"
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

**Webhook Payload (успех):**
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
      "download_url": "http://video-processor:5001/download/abc123/output/output.mp4",
      "download_path": "/download/abc123/output/output.mp4"
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

**Webhook Payload (ошибка):**
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

### Жизненный цикл статусов

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

## 📖 Примеры

### Пример 1: Shorts с автоматической нарезкой (start_time/end_time)

```json
{
  "video_url": "https://example.com/long-video.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "to_shorts",
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

### Пример 2: Извлечение аудио с chunking для Whisper API

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

**Response:**
```json
{
  "task_id": "xyz123",
  "event": "task_completed",
  "status": "completed",
  "output_files": [
    {
      "filename": "audio_chunk000.mp3",
      "file_size": 24641536,
      "file_size_mb": 23.5,
      "chunk": "1:3",
      "download_url": "http://video-processor:5001/download/xyz123/output/audio_chunk000.mp3"
    },
    {
      "filename": "audio_chunk001.mp3",
      "file_size": 24330240,
      "file_size_mb": 23.2,
      "chunk": "2:3",
      "download_url": "http://video-processor:5001/download/xyz123/output/audio_chunk001.mp3"
    },
    {
      "filename": "audio_chunk002.mp3",
      "file_size": 18980864,
      "file_size_mb": 18.1,
      "chunk": "3:3",
      "download_url": "http://video-processor:5001/download/xyz123/output/audio_chunk002.mp3"
    }
  ],
  "total_files": 3,
  "is_chunked": true,
  "completed_at": "2025-11-12T19:45:23"
}
```

**Параметры extract_audio:**
- `format`: `mp3` (default) или `aac`
- `bitrate`: `128k`, `192k` (default), `256k`, `320k`
- `chunk_duration_minutes`: Длительность чанка в минутах
- `max_chunk_size_mb`: Макс. размер чанка в МБ (default: 24)
- `optimize_for_whisper`: `true` - оптимизация для Whisper API (16kHz, mono, 64k bitrate)

---

## 🔧 Конфигурация

### Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `API_KEY` | `None` | Bearer token для аутентификации. Если задан, включает публичный API режим с защищенными endpoints. Если не задан, работает во внутреннем режиме без аутентификации. |
| `PUBLIC_BASE_URL` | `None` | Внешний базовый URL для download ссылок (например, `https://domain.com/api`). Используется только когда `API_KEY` задан. Игнорируется во внутреннем режиме. |
| `WORKERS` | `1` | Количество gunicorn workers (используйте 2+ с Redis для multi-worker режима) |
| `REDIS_HOST` | `redis` | Redis hostname для multi-worker хранилища задач |
| `REDIS_PORT` | `6379` | Redis порт |
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

## 📝 Хранение файлов

- **Task directories**: Автоматически удаляются через **2 часа** после создания
- **Input/Temp files**: Удаляются сразу после завершения обработки
- **Output files**: Хранятся 2 часа в `/app/tasks/{task_id}/output/`
- **Redis Tasks**: TTL = 24 часа

---

## 💡 Советы по интеграции

- `output_files`: всегда массив. Даже при одном файле используйте итерацию.
- `is_chunked`: определяйте пакетную обработку по этому флагу и/или наличию `chunk`.
- `chunk` формат: строка `"i:n"`, где `i` — 1-базовый индекс, `n` — общее число частей.
- `client_meta`: передайте произвольный JSON — он вернётся как есть в ответах, вебхуках и `metadata.json`.
- Ссылки скачивания: используйте `download_url` для публичного доступа и `download_path` для внутренних вызовов.
- Метаданные: `metadata_url` содержит полный снимок результата — удобно для кэширования.
- Вебхуки: обрабатывайте оба события — `task_completed` и `task_failed`.
- TTL: файлы хранятся 2 часа; скачайте/переложите в постоянное хранилище сразу после `completed`.

---

## 🛠 Разработка

### Local Build

```bash
git clone https://github.com/alexbic/video-processor-api.git
cd video-processor-api
docker build -t video-processor-api:local .
docker run -d -p 5001:5001 video-processor-api:local
```

### Тестирование

```bash
# Health check
curl http://localhost:5001/health

# Список шрифтов
curl http://localhost:5001/fonts

# Тестовый запрос
curl -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "https://example.com/video.mp4", "operations": [{"type": "to_shorts"}]}'
```

---

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) для подробностей.

---

## 🤝 Contributing

Pull requests приветствуются! Для больших изменений сначала откройте issue.

---

## 📧 Контакты

- GitHub: [@alexbic](https://github.com/alexbic)
- Issues: [GitHub Issues](https://github.com/alexbic/video-processor-api/issues)
