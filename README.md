# Video Processor API

REST API для обработки видео с FFmpeg. Создание вертикальных Shorts с субтитрами, нарезка видео, извлечение аудио.

[![Docker Hub](https://img.shields.io/docker/v/alexbic/video-processor-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/alexbic/video-processor-api)
[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-image-blue?logo=github)](https://github.com/alexbic/video-processor-api/pkgs/container/video-processor-api)
[![Build Status](https://img.shields.io/github/actions/workflow/status/alexbic/video-processor-api/docker-build.yml?branch=main)](https://github.com/alexbic/video-processor-api/actions)

## Features

- ⚡ Async processing - параллельная обработка множества клипов
- 📦 Letterbox mode - горизонтальное видео с размытым фоном
- 📝 Динамические субтитры - автосубтитры из Whisper API с таймкодами
- 🎨 Текстовые оверлеи - заголовки с fade-эффектами
- 🎵 Извлечение аудио - автоматическое разбиение на чанки < 25 МБ
- ✂️ Нарезка видео - по таймкодам с конвертацией в Shorts (1080x1920)

## Installation

```bash
docker pull alexbic/video-processor-api:latest
docker run -d -p 5001:5001 --name video-processor alexbic/video-processor-api:latest
```

## API Reference

### Health Check

```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "video-processor-api"
}
```

---

### Extract Audio

Извлечь аудио из видео. Автоматически разбивает на чанки если файл > 25 МБ.

**Request:**
```bash
curl -X POST http://localhost:5001/extract_audio \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "http://youtube_downloader:5000/download_file/video.mp4"
  }'
```

**Response (single file):**
```json
{
  "success": true,
  "mode": "single",
  "download_url": "http://video-processor:5001/download/audio_20250115_103000.mp3",
  "file_size_mb": 15.5,
  "whisper_ready": true
}
```

**Response (chunked):**
```json
{
  "success": true,
  "mode": "chunked",
  "total_chunks": 3,
  "chunks": [
    {
      "chunk_index": 0,
      "download_url": "http://video-processor:5001/download/audio_xxx_chunk000.mp3",
      "start_time": 0.0,
      "end_time": 630.0,
      "file_size_mb": 24.0
    }
  ]
}
```

---

### Create Short (Async) - Recommended

Создать вертикальный Short асинхронно. Возвращает task_id мгновенно.

#### Базовый пример (без текста)

```bash
curl -X POST http://localhost:5001/process_to_shorts_async \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "http://youtube_downloader:5000/download_file/video.mp4",
    "start_time": 10.5,
    "end_time": 45.2,
    "crop_mode": "letterbox"
  }'
```

#### С заголовком

```bash
curl -X POST http://localhost:5001/process_to_shorts_async \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "http://youtube_downloader:5000/download_file/video.mp4",
    "start_time": 50.0,
    "end_time": 80.5,
    "crop_mode": "letterbox",
    "title_text": "Невероятный трюк!"
  }'
```

#### С динамическими субтитрами (полный пример)

```bash
curl -X POST http://localhost:5001/process_to_shorts_async \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "http://youtube_downloader:5000/download_file/video.mp4",
    "start_time": 125.5,
    "end_time": 165.8,
    "crop_mode": "letterbox",
    "title_text": "Эпичный момент!",
    "subtitles": [
      {"text": "Смотрите что", "start": 0.0, "end": 1.2},
      {"text": "я сейчас сделаю", "start": 1.3, "end": 2.5},
      {"text": "это будет нереально", "start": 2.6, "end": 4.8}
    ],
    "title_config": {
      "fontsize": 60,
      "fontcolor": "white",
      "bordercolor": "black",
      "borderw": 3,
      "y": 100,
      "start_time": 0.5,
      "duration": 4,
      "fade_in": 0.5,
      "fade_out": 0.5
    },
    "subtitle_config": {
      "fontsize": 48,
      "fontcolor": "#90EE90",
      "bordercolor": "white",
      "borderw": 3,
      "y": "h-150"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "queued",
  "check_status_url": "/task_status/a1b2c3d4-5678-90ab-cdef-1234567890ab"
}
```

---

### Check Task Status

```bash
curl http://localhost:5001/task_status/a1b2c3d4-5678-90ab-cdef-1234567890ab
```

**Response (processing):**
```json
{
  "success": true,
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "processing",
  "progress": 65
}
```

**Response (completed):**
```json
{
  "success": true,
  "task_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "status": "completed",
  "progress": 100,
  "download_url": "http://video-processor:5001/download/shorts_xxx.mp4",
  "file_size": 12582912
}
```

---

### Download File

```bash
curl -O http://localhost:5001/download/shorts_xxx.mp4
```

---

## Parameters Reference

### crop_mode

| Value | Description |
|-------|-------------|
| `letterbox` | ✅ Recommended - горизонтальное видео с размытым фоном |
| `center` | Обрезка по центру |
| `top` | Обрезка сверху |
| `bottom` | Обрезка снизу |

### title_config

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fontsize` | int | 60 | Размер шрифта |
| `fontcolor` | string | "white" | Цвет текста |
| `bordercolor` | string | "black" | Цвет обводки |
| `borderw` | int | 3 | Толщина обводки |
| `y` | int/string | 100 | Позиция по вертикали |
| `start_time` | float | 0.5 | Когда появляется (сек) |
| `duration` | float | 4 | Длительность (сек) |
| `fade_in` | float | 0.5 | Fade in (сек) |
| `fade_out` | float | 0.5 | Fade out (сек) |

### subtitle_config

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fontsize` | int | 48 | Размер шрифта |
| `fontcolor` | string | "#90EE90" | Цвет текста (светло-зеленый) |
| `bordercolor` | string | "white" | Цвет обводки |
| `borderw` | int | 3 | Толщина обводки |
| `y` | string | "h-150" | Позиция (150px от низа) |

### subtitles array

Массив объектов с полями:
- `text` (string) - текст субтитра
- `start` (float) - начало **относительно клипа** (сек)
- `end` (float) - конец **относительно клипа** (сек)

**⚠️ ВАЖНО:** Timestamps должны быть **относительные** от начала клипа (0-based), не абсолютные!

---

## Preset Configurations

### Цветовые схемы субтитров

```bash
# Светло-зеленый (по умолчанию)
"subtitle_config": {"fontcolor": "#90EE90", "bordercolor": "white"}

# Желтый (TikTok style)
"subtitle_config": {"fontcolor": "yellow", "bordercolor": "black"}

# Белый классический
"subtitle_config": {"fontcolor": "white", "bordercolor": "black"}

# Неоновый розовый
"subtitle_config": {"fontcolor": "#FF69B4", "bordercolor": "white"}
```

### Позиционирование

```bash
# Внизу (по умолчанию)
"y": "h-150"

# Выше от низа
"y": "h-200"

# По центру
"y": "(h-text_h)/2"

# Вверху под title
"y": "200"
```

---

## n8n Integration

### Full Workflow

```
YouTube Downloader
  ↓ download_url
Extract Audio
  ↓ audio file
Whisper API (timestamp_granularities: "word")
  ↓ words: [{word, start, end}]
LLM (Gemini/GPT) - см. llm-prompts/shorts-extractor.md
  ↓ shorts: [{start, end, title, subtitles}]
Process to Shorts Async (параллельно для всех клипов)
  ↓ task_ids
Check Status (loop)
  ↓ download_urls
Download & Publish
```

### Code Nodes

**Prepare Whisper data for LLM:**
```javascript
const words_llm = $json.words.map(w => ({w: w.word, s: w.start, e: w.end}));
return [{json: {
  video_duration: $json.duration,
  text_llm: $json.text,
  words_llm: words_llm,
  source_video_url: $json.source_video_url
}}];
```

**Process LLM response:**
```javascript
const response = $json;
const shorts = response.shorts || [];

const title_config = {
  fontsize: 60,
  fontcolor: "white",
  bordercolor: "black",
  borderw: 3,
  y: 100,
  start_time: 0.5,
  duration: 4,
  fade_in: 0.5,
  fade_out: 0.5
};

const subtitle_config = {
  fontsize: 48,
  fontcolor: "#90EE90",
  bordercolor: "white",
  borderw: 3,
  y: "h-150"
};

const requests = shorts.map((short, index) => ({
  video_url: response.source_video_url,
  start_time: short.start,
  end_time: short.end,
  crop_mode: "letterbox",
  title_text: short.title,
  subtitles: short.subtitles,
  title_config: title_config,
  subtitle_config: subtitle_config,
  metadata: {
    tiktok_description: short.video_description_for_tiktok,
    instagram_description: short.video_description_for_instagram,
    youtube_title: short.video_title_for_youtube_short,
    clip_index: index + 1,
    total_clips: shorts.length
  }
}));

return requests.map(req => ({ json: req }));
```

---

## Troubleshooting

**Субтитры не синхронны**
→ Timestamps должны быть относительные (0-based), не абсолютные. LLM должен вычесть `clip.start`.

**Слишком много текста**
→ Уменьшите количество слов в фразе (2-4) или `fontsize` до 42-44.

**Плохая контрастность**
→ Увеличьте `borderw` до 4-5 или смените `bordercolor`.

**Timeout**
→ Используйте `/process_to_shorts_async` вместо sync версии.

---

## Additional Resources

- [LLM Prompt для выделения моментов](llm-prompts/shorts-extractor.md)
- [YouTube Downloader API](https://github.com/alexbic/youtube-downloader-api)

---

## License

MIT License
