# Video Processor API

Мощный REST API для обработки видео с использованием FFmpeg. Извлечение аудио, нарезка видео по таймкодам и конвертация в формат Shorts (вертикальная ориентация 1080x1920).

[![Docker Hub](https://img.shields.io/docker/v/alexbic/video-processor-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/alexbic/video-processor-api)
[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-image-blue?logo=github)](https://github.com/alexbic/video-processor-api/pkgs/container/video-processor-api)
[![Build Status](https://img.shields.io/github/actions/workflow/status/alexbic/video-processor-api/docker-build.yml?branch=main)](https://github.com/alexbic/video-processor-api/actions)

## Возможности

- **Извлечение аудио** из видео в MP3 формат
- **Автоматическое разбиение аудио на чанки** для Whisper API (< 25 МБ каждый)
- **Нарезка видео** по таймкодам (start_time, end_time)
- **Конвертация в Shorts** - вертикальная ориентация 1080x1920 для YouTube Shorts и TikTok
- **Комбинированная обработка** - нарезка + конвертация в один запрос
- Автоматическая очистка файлов старше 2 часов
- Health check endpoint для мониторинга
- Поддержка платформ: linux/amd64, linux/arm64

## Установка

### Из Docker Hub

```bash
docker pull alexbic/video-processor-api:latest
```

### Из GitHub Container Registry

```bash
docker pull ghcr.io/alexbic/video-processor-api:latest
```

## Быстрый старт

### Запуск через Docker

```bash
docker run -d -p 5001:5001 --name video-processor alexbic/video-processor-api:latest
```

### Запуск через Docker Compose

```yaml
version: '3.8'
services:
  video-processor:
    image: alexbic/video-processor-api:latest
    # или используйте GitHub Container Registry:
    # image: ghcr.io/alexbic/video-processor-api:latest
    ports:
      - "5001:5001"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    restart: unless-stopped
```

## API Endpoints

### 1. Health Check

```bash
GET /health
```

Ответ:
```json
{
  "status": "healthy",
  "service": "video-processor-api",
  "timestamp": "2025-01-15T10:30:00.123456"
}
```

### 2. Извлечь аудио из видео

#### Вариант А: Обычное извлечение (файл < 25 МБ)

```bash
POST /extract_audio
Content-Type: application/json

{
  "video_url": "http://youtube_downloader:5000/download_file/video_20240115_103000.mp4"
}
```

Ответ (mode: "single"):
```json
{
  "success": true,
  "mode": "single",
  "filename": "audio_20250115_103000.mp3",
  "file_path": "/app/outputs/audio_20250115_103000.mp3",
  "file_size": 5242880,
  "file_size_mb": 5.0,
  "duration": 180.5,
  "download_url": "http://video_processor:5001/download/audio_20250115_103000.mp3",
  "download_path": "/download/audio_20250115_103000.mp3",
  "whisper_ready": true,
  "note": "Audio file will auto-delete after 2 hours.",
  "processed_at": "2025-01-15T10:30:00.123456"
}
```

#### Вариант Б: Автоматическое разбиение на чанки (файл > 25 МБ) ⭐

**Для длинных видео:** API автоматически разобьет аудио на чанки, если размер превышает 25 МБ.

```bash
POST /extract_audio
Content-Type: application/json

{
  "video_url": "http://youtube_downloader:5000/download_file/video_20240115_103000.mp4"
}
```

Ответ (mode: "chunked", если файл > 25 МБ):
```json
{
  "success": true,
  "mode": "chunked",
  "total_duration": 1800.0,
  "total_chunks": 3,
  "chunk_duration_minutes": 10.5,
  "chunks": [
    {
      "chunk_index": 0,
      "filename": "audio_20250115_103000_chunk000.mp3",
      "file_size": 15728640,
      "file_size_mb": 15.0,
      "start_time": 0.0,
      "end_time": 630.0,
      "duration": 630.0,
      "download_url": "http://video_processor:5001/download/audio_20250115_103000_chunk000.mp3",
      "download_path": "/download/audio_20250115_103000_chunk000.mp3",
      "whisper_ready": true
    },
    {
      "chunk_index": 1,
      "filename": "audio_20250115_103000_chunk001.mp3",
      "file_size": 15728640,
      "file_size_mb": 15.0,
      "start_time": 630.0,
      "end_time": 1260.0,
      "duration": 630.0,
      "download_url": "http://video_processor:5001/download/audio_20250115_103000_chunk001.mp3",
      "download_path": "/download/audio_20250115_103000_chunk001.mp3",
      "whisper_ready": true
    },
    {
      "chunk_index": 2,
      "filename": "audio_20250115_103000_chunk002.mp3",
      "file_size": 14155776,
      "file_size_mb": 13.5,
      "start_time": 1260.0,
      "end_time": 1800.0,
      "duration": 540.0,
      "download_url": "http://video_processor:5001/download/audio_20250115_103000_chunk002.mp3",
      "download_path": "/download/audio_20250115_103000_chunk002.mp3",
      "whisper_ready": true
    }
  ],
  "note": "Audio split into 3 chunks. Each chunk optimized for Whisper API (<25MB). Files will auto-delete after 2 hours.",
  "processed_at": "2025-01-15T10:30:00.123456"
}
```

#### Вариант В: Ручная настройка размера и длительности чанков

```bash
POST /extract_audio
Content-Type: application/json

{
  "video_url": "http://youtube_downloader:5000/download_file/video_20240115_103000.mp4",
  "chunk_duration_minutes": 10,
  "max_chunk_size_mb": 20
}
```

Параметры:
- `chunk_duration_minutes` (опциональный) - длительность каждого чанка в минутах (приоритет над max_chunk_size_mb)
- `max_chunk_size_mb` (опциональный) - максимальный размер чанка в МБ (по умолчанию: 24)
  - Для Whisper API: используйте 24 (лимит 25 МБ)
  - Для других целей: задайте любой размер (например, 10, 15, 20 МБ)
  - Если файл превышает этот размер → автоматически разобьется

**Примеры использования:**

```bash
# Whisper API (по умолчанию)
{"video_url": "..."}  # max_chunk_size_mb = 24

# Меньшие чанки для быстрой обработки
{"video_url": "...", "max_chunk_size_mb": 15}

# Фиксированная длительность чанков
{"video_url": "...", "chunk_duration_minutes": 5}

# Комбинация (chunk_duration имеет приоритет)
{"video_url": "...", "chunk_duration_minutes": 10, "max_chunk_size_mb": 20}
```

**Когда используется chunking:**
- Файл > `max_chunk_size_mb` → автоматически разобьется
- Указан `chunk_duration_minutes` → принудительное разбиение
- По умолчанию: если файл > 24 МБ → разбивается автоматически

**Использование в n8n:**

**Шаг 1: HTTP Request - Extract Audio**
```
Method: POST
URL: http://video_processor:5001/extract_audio
Body: {"video_url": "{{ $json.download_url }}"}
Response Format: JSON
```

**Шаг 2: IF Node - Проверить режим**
```
Condition: {{ $json.mode }} равно "single" или "chunked"
```

**Шаг 3а: Одиночный файл (mode = "single")**
```
HTTP Request:
Method: GET
URL: {{ $json.download_url }}
Response Format: File
Binary Property: data

→ Whisper API
```

**Шаг 3б: Чанки (mode = "chunked") → Loop через chunks массив**
```
1. Split Out Node: разбить chunks массив
2. HTTP Request для каждого чанка:
   Method: GET
   URL: {{ $json.download_url }}
   Response Format: File
   Binary Property: data
3. Whisper API для каждого чанка
4. Aggregate Node: собрать все транскрипции
5. Code Node: объединить с учетом start_time каждого чанка
```

**Пример Code Node для объединения транскрипций:**
```javascript
// Объединяем транскрипции из всех чанков
const allSegments = [];

for (const item of $input.all()) {
  const chunkIndex = item.json.chunk_index;
  const startTime = item.json.start_time; // Смещение времени чанка
  const whisperResponse = item.json.whisper_result;

  // Добавляем смещение времени к каждому сегменту
  for (const segment of whisperResponse.segments) {
    allSegments.push({
      start: segment.start + startTime,
      end: segment.end + startTime,
      text: segment.text
    });
  }
}

// Сортируем по времени
allSegments.sort((a, b) => a.start - b.start);

return [{ json: { segments: allSegments } }];
```

### 3. Нарезать видео по таймкодам

```bash
POST /cut_video
Content-Type: application/json

{
  "video_url": "http://youtube_downloader:5000/download_file/video_20240115_103000.mp4",
  "start_time": 10,
  "end_time": 70
}
```

Параметры:
- `video_url` (обязательный) - URL видеофайла
- `start_time` (обязательный) - начало в секундах (например: 10) или формате HH:MM:SS
- `end_time` (обязательный) - конец в секундах (например: 70) или формате HH:MM:SS

Ответ:
```json
{
  "success": true,
  "filename": "cut_20250115_103000.mp4",
  "file_path": "/app/outputs/cut_20250115_103000.mp4",
  "file_size": 15728640,
  "download_url": "http://video_processor:5001/download/cut_20250115_103000.mp4",
  "download_path": "/download/cut_20250115_103000.mp4",
  "start_time": 10,
  "end_time": 70,
  "note": "Video file will auto-delete after 2 hours.",
  "processed_at": "2025-01-15T10:30:00.123456"
}
```

### 4. Конвертировать в формат Shorts

```bash
POST /convert_to_shorts
Content-Type: application/json

{
  "video_url": "http://video_processor:5001/download/cut_20250115_103000.mp4",
  "crop_mode": "center"
}
```

Параметры:
- `video_url` (обязательный) - URL видеофайла
- `crop_mode` (опциональный) - режим обрезки: `center` (по центру), `top` (сверху), `bottom` (снизу). По умолчанию: `center`

Ответ:
```json
{
  "success": true,
  "filename": "shorts_20250115_103000.mp4",
  "file_path": "/app/outputs/shorts_20250115_103000.mp4",
  "file_size": 12582912,
  "download_url": "http://video_processor:5001/download/shorts_20250115_103000.mp4",
  "download_path": "/download/shorts_20250115_103000.mp4",
  "resolution": "1080x1920",
  "format": "shorts",
  "crop_mode": "center",
  "note": "Shorts video will auto-delete after 2 hours.",
  "processed_at": "2025-01-15T10:30:00.123456"
}
```

### 5. Обработать в Shorts (нарезка + конвертация за один запрос) ⭐

```bash
POST /process_to_shorts
Content-Type: application/json

{
  "video_url": "http://youtube_downloader:5000/download_file/video_20240115_103000.mp4",
  "start_time": 10,
  "end_time": 70,
  "crop_mode": "center"
}
```

Этот endpoint объединяет нарезку и конвертацию в один шаг. Рекомендуется для n8n workflow.

Ответ:
```json
{
  "success": true,
  "filename": "shorts_20250115_103000.mp4",
  "file_path": "/app/outputs/shorts_20250115_103000.mp4",
  "file_size": 12582912,
  "download_url": "http://video_processor:5001/download/shorts_20250115_103000.mp4",
  "download_path": "/download/shorts_20250115_103000.mp4",
  "resolution": "1080x1920",
  "format": "shorts",
  "crop_mode": "center",
  "start_time": 10,
  "end_time": 70,
  "note": "Shorts video will auto-delete after 2 hours.",
  "processed_at": "2025-01-15T10:30:00.123456"
}
```

### 6. Скачать файл

```bash
GET /download/<filename>
```

Возвращает файл для скачивания.

## n8n Workflow для создания Shorts

### Полный процесс обработки:

```
1. Trigger (YouTube URL)
   ↓
2. HTTP Request → YouTube Downloader API /download_direct
   → Скачать видео
   ↓
3. HTTP Request → Video Processor API /extract_audio
   → Извлечь аудио (автоматически разобьется на чанки если > 25MB)
   ↓
4. IF Node → Проверить mode: "single" или "chunked"
   ↓
   ├─► mode = "single":
   │   └─► HTTP Request → Скачать аудио (Binary)
   │       └─► Whisper API
   │
   └─► mode = "chunked":
       └─► Split Out Node (chunks array)
           └─► Loop через каждый chunk:
               ├─► HTTP Request → Скачать chunk (Binary)
               ├─► Whisper API → Транскрибация чанка
               └─► Aggregate Node → Собрать все результаты
                   └─► Code Node → Объединить с учетом start_time
   ↓
5. Code Node → Обработать результаты Whisper
   → Найти интересные моменты с таймкодами
   ↓
6. Loop через найденные сегменты:
   HTTP Request → Video Processor API /process_to_shorts
   → Создать Short для каждого сегмента
   ↓
7. HTTP Request → Скачать каждый Short (Binary)
   ↓
8. HTTP Request → upload-post API
   → Загрузить в TikTok/YouTube Shorts
```

### Пример n8n Node для создания Shorts

**HTTP Request Node (Создать Short):**
```
Method: POST
URL: http://video_processor:5001/process_to_shorts
Body:
{
  "video_url": "{{ $('YouTube Downloader').item.json.download_url }}",
  "start_time": {{ $json.start }},
  "end_time": {{ $json.end }},
  "crop_mode": "center"
}
Response Format: JSON
```

**HTTP Request Node (Скачать Short):**
```
Method: GET
URL: {{ $json.download_url }}
Response Format: File
Binary Property: data
```

## Примеры использования

### cURL

```bash
# Извлечь аудио
curl -X POST http://localhost:5001/extract_audio \
  -H "Content-Type: application/json" \
  -d '{"video_url": "http://youtube_downloader:5000/download_file/video.mp4"}'

# Нарезать видео
curl -X POST http://localhost:5001/cut_video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "http://youtube_downloader:5000/download_file/video.mp4", "start_time": 10, "end_time": 70}'

# Конвертировать в Shorts
curl -X POST http://localhost:5001/convert_to_shorts \
  -H "Content-Type: application/json" \
  -d '{"video_url": "http://video_processor:5001/download/cut.mp4", "crop_mode": "center"}'

# Создать Short за один запрос
curl -X POST http://localhost:5001/process_to_shorts \
  -H "Content-Type: application/json" \
  -d '{"video_url": "http://youtube_downloader:5000/download_file/video.mp4", "start_time": 10, "end_time": 70, "crop_mode": "center"}'
```

### Python

```python
import requests

# Извлечь аудио
response = requests.post('http://localhost:5001/extract_audio', json={
    'video_url': 'http://youtube_downloader:5000/download_file/video.mp4'
})
audio_data = response.json()
print(f"Audio URL: {audio_data['download_url']}")

# Создать Short
response = requests.post('http://localhost:5001/process_to_shorts', json={
    'video_url': 'http://youtube_downloader:5000/download_file/video.mp4',
    'start_time': 10,
    'end_time': 70,
    'crop_mode': 'center'
})
short_data = response.json()
print(f"Short URL: {short_data['download_url']}")
```

## Разработка

### Локальная сборка

```bash
git clone https://github.com/alexbic/video-processor-api.git
cd video-processor-api
docker build -t video-processor-api .
docker run -p 5001:5001 video-processor-api
```

### Локальный запуск без Docker

```bash
# Установка FFmpeg (macOS)
brew install ffmpeg

# Установка зависимостей
pip install -r requirements.txt

# Запуск
python app.py
```

## CI/CD

Проект настроен с автоматической сборкой и публикацией через GitHub Actions.

При каждом push в `main` ветку автоматически:
1. Собирается Docker образ для платформ linux/amd64 и linux/arm64
2. Публикуется на Docker Hub: `alexbic/video-processor-api`
3. Публикуется на GitHub Container Registry: `ghcr.io/alexbic/video-processor-api`
4. Обновляется описание на Docker Hub

Статус сборки можно посмотреть на [странице Actions](https://github.com/alexbic/video-processor-api/actions)

## Технологии

- Python 3.11
- Flask 3.0.0
- FFmpeg (latest)
- Gunicorn
- Docker

## Troubleshooting

### Ошибка: "413: Maximum content size limit exceeded" при Whisper API

**Причина**: Аудиофайл превышает лимит Whisper API в 25 МБ.

**Решение**: API автоматически разбивает файлы > 25 МБ на чанки! Просто используйте `/extract_audio` без дополнительных параметров:

```bash
POST /extract_audio
{"video_url": "..."}
```

API вернет `mode: "chunked"` с массивом чанков, каждый < 25 МБ.

**n8n workflow:**
1. Extract Audio → получить ответ
2. IF Node: проверить `mode` ("single" или "chunked")
3. Если "chunked": использовать Split Out Node на `chunks` массив
4. Loop через каждый chunk → Whisper API
5. Aggregate → Code Node для объединения с учетом `start_time`

**Ручная настройка чанков:**
```json
{
  "video_url": "...",
  "chunk_duration_minutes": 10,
  "max_chunk_size_mb": 24
}
```

### Ошибка: "File too large" при обработке

**Причина**: Таймаут gunicorn по умолчанию - 30 секунд.

**Решение**: В Dockerfile уже установлен таймаут 600 секунд (10 минут). Для локального запуска:
```bash
gunicorn --timeout 600 app:app
```

### Ошибка: FFmpeg "Invalid argument"

**Причина**: Неверный формат таймкодов.

**Решение**: Используйте секунды (например: 10, 70) или формат HH:MM:SS (например: "00:00:10", "00:01:10")

### Видео обрезано не по центру

**Решение**: Используйте параметр `crop_mode`:
- `center` - обрезка по центру (по умолчанию)
- `top` - обрезка сверху
- `bottom` - обрезка снизу

## Интеграция с YouTube Downloader API

Эти два API отлично работают вместе:

```yaml
version: '3.8'
services:
  youtube-downloader:
    image: alexbic/youtube-downloader-api:latest
    ports:
      - "5000:5000"
    volumes:
      - ./downloads:/app/downloads
    restart: unless-stopped

  video-processor:
    image: alexbic/video-processor-api:latest
    ports:
      - "5001:5001"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    restart: unless-stopped
```

## Безопасность

- API не хранит персональные данные
- Файлы автоматически удаляются через 2 часа
- Рекомендуется использовать за reverse proxy (nginx/traefik)
- Добавьте rate limiting для production использования

## Лицензия

MIT License

## Поддержка

Если возникли проблемы:
1. Проверьте логи контейнера: `docker logs <container_id>`
2. Убедитесь что video_url доступен
3. Проверьте наличие свободного места для файлов
4. Создайте issue в GitHub repository

## TODO

- [ ] Добавить аутентификацию (API keys)
- [ ] Добавить queue для длительных задач (Celery)
- [ ] Добавить progress tracking для обработки
- [ ] Поддержка batch processing (несколько сегментов за раз)
- [ ] Добавить субтитры на видео
- [ ] Webhook уведомления при завершении обработки
- [ ] S3/MinIO storage для файлов

## Автор

Создано с использованием FFmpeg и Flask

## Disclaimer

Этот инструмент предназначен для личного использования. Убедитесь, что вы соблюдаете авторские права при обработке контента.
