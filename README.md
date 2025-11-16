# Video Processor API

**Open Source** REST API for video processing with FFmpeg. Create vertical Shorts, add subtitles, cut videos, extract audio.

[![Docker Hub](https://img.shields.io/docker/v/alexbic/video-processor-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/alexbic/video-processor-api)
[![GitHub](https://img.shields.io/badge/GitHub-alexbic/video--processor--api-blue?logo=github)](https://github.com/alexbic/video-processor-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](RELEASE_NOTES_v1.1.0.md)

**English** | [Русский](README.ru.md)

---

## ✨ Features

- 🎬 **Pipeline Processing** - chain multiple operations (letterbox → title → subtitles)
- 📦 **Letterbox Mode** - convert horizontal videos to vertical format (1080x1920) with blurred background
- 📝 **Dynamic Subtitles** - with custom fonts, colors, and positioning
- 🎨 **Text Overlays** - titles with fade effects
- ✂️ **Video Cutting** - by timecodes with Shorts conversion
- 🎵 **Audio Extraction** - from video files
- 📡 **Webhooks** - completion notifications with retry logic
- ⚡ **Async Processing** - background processing with status tracking
- 🔠 **Custom Fonts** - support for uploading custom fonts (.ttf/.otf)
- 🐳 **Redis Support** - multi-worker mode for high loads
- 🛡️ **Input Validation** - automatic media file validation before processing
- 🔗 **Full URLs** - absolute links in all responses for n8n/external integrations

---

## 🚀 Quick Start

### Single Worker (without Redis)

```bash
docker pull alexbic/video-processor-api:latest
docker run -d -p 5001:5001 \
  -v $(pwd)/tasks:/app/tasks \
  --name video-processor \
  alexbic/video-processor-api:latest
```

### Multi-Worker with Redis (recommended for production)

See [docker-compose.redis-example.yml](docker-compose.redis-example.yml) for full configuration.

```bash
docker-compose up -d redis video-processor
```

API automatically detects Redis availability:
- **With Redis**: Multi-worker mode (2+ workers)
- **Without Redis**: Single-worker mode (fallback)

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

Add a `client_meta` field (any JSON object) to your request, and it will be:
- saved in the task's `metadata.json`,
- included in `/process_video` (sync) and `/task_status/{task_id}` (async) responses,
- sent in webhook payloads (`task_completed`/`task_failed`).

This is useful for titles/captions for different social networks, campaign IDs, trace-ids, etc.

Example request with `client_meta`:
```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "async",
  "operations": [{"type": "make_short", "crop_mode": "letterbox"}],
  "client_meta": {
    "titles": {
      "tiktok": "Cool AI Video",
      "youtube": "Amazing AI Demo",
      "instagram": "AI in Action"
    },
    "campaign_id": "cmp-2025-11-13"
  }
}
```
In responses, the field will be available as `client_meta` unchanged.

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

- `GET /health` — service status (versions, `storage_mode`, Redis availability) **[no authorization]**
- `GET /fonts` — list of system and custom fonts **[requires API key]**
- `POST /process_video` — start pipeline (sync/async; `operations`, optionally `webhook_url`) **[requires API key]**
- `GET /task_status/{task_id}` — task status (`queued`/`processing`/`completed`/`error`) **[no authorization]**
- `GET /tasks` — recent tasks (for debugging) **[requires API key]**
- `GET /download/{task_id}/{filename}` — download completed file **[no authorization]**
- `GET /download/{task_id}/metadata.json` — result metadata **[no authorization]**

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

### Available Fonts

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

**Custom Fonts:**
1. Place .ttf/.otf files in `/opt/n8n-docker/volumes/video_processor/fonts/`
2. Restart the container
3. Use via `"font": "YourFontName"`

See [FONTS.md](FONTS.md) for details.

---

### Video Processing

`POST /process_video`

Use ready-made operations for video processing:

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

**Available operations:**
- `cut_video` - cut video by timecodes
- `make_short` - convert to Shorts format (letterbox + title + subtitles); supports `start_time`/`end_time` for automatic cutting
- `extract_audio` - extract audio track

---

### Response Format

**Unified format** - all operations return the same structure:

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

**Key fields:**
- `video_url` - original video URL that was processed
- `output_files` - **always an array** (even if 1 file)
- `is_chunked` - `true` if files are split into chunks (for Whisper API)
- `total_files` - total number of files

### Error Responses

All errors are returned with an HTTP code, `status: "error"` field and message in `error`.

- 400 Bad Request (validation):
  ```json
  { "status": "error", "error": "video_url is required" }
  ```
- 404 Not Found (task status):
  ```json
  { "status": "error", "error": "Task not found" }
  ```
- 403 Forbidden (downloading file outside task directory):
  ```json
  { "status": "error", "error": "Invalid file path" }
  ```
- 404 Not Found (file not found during download):
  ```json
  { "status": "error", "error": "File not found" }
  ```
- 500 Internal Server Error (execution error):
  ```json
  { "status": "error", "error": "FFmpeg error: ..." }
  ```

In webhooks on error, event remains `event: "task_failed"`, and status is `status: "error"`.

**For chunked files** (extract_audio with splitting):
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

#### Sync (synchronous)

```json
{
  "execution": "sync"
}
```

**Response (immediately):**
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

#### Async (asynchronous)

```json
{
  "execution": "async"
}
```

**Response (immediately):**
```json
{
  "task_id": "abc123",
  "status": "processing",
  "message": "Task created and processing in background"
}
```

**Check status:**
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

Add `webhook_url` to receive notifications:

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

**Retry logic:**
- 3 send attempts
- Exponential backoff: 1s, 2s, 4s

---

### Status Lifecycle

Task statuses and transitions:

- `queued` → task created and queued (async)
- `processing` → operations executing (`progress` 5–95%)
- `completed` → finished; `output_files`, `is_chunked`, `metadata_url`, `video_url` available
- `error` → execution error; `error` — description, `failed_at` — timestamp

Key status fields:
- `task_id`: task identifier
- `status`: `queued` | `processing` | `completed` | `error`
- `progress`: 0–100 (for async)
- `created_at` / `completed_at` / `failed_at`: timestamps
- `output_files`: always an array; when chunked contains `chunk: "i:n"`
- `is_chunked`: `true` if `output_files` has `chunk` field

Polling recommendations:
- Poll `GET /task_status/{task_id}` every 2–3 seconds
- Stop polling when `status` is {`completed`, `error`}

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

### Example 1: Shorts with automatic cutting (start_time/end_time)

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
        "text": "My First Shorts",
        "font": "DejaVu Sans Bold",
        "fontsize": 70,
        "fontcolor": "white"
      },
      "subtitles": {
        "items": [
          {"text": "First subtitle", "start": 0, "end": 3}
        ],
        "font": "Roboto",
        "fontsize": 64,
        "fontcolor": "yellow"
      }
    }
  ]
}
```

**Note:** `start_time` and `end_time` can be numbers (seconds) or strings (`"00:01:30"`). When both parameters are specified, the fragment will be cut automatically.

**Field format:**
- `title` — object with `text` field and font settings
- `subtitles` — object with `items` field (array of subtitles) and font settings

### Example 2: Simple Shorts conversion (without cutting)

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

### Example 3: Shorts with title and subtitles

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

### Example 4: Video cutting

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

### Example 5: Pipeline - multiple operations

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

### Example 6: Audio extraction (sync mode)

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

**Response (sync - returned immediately after completion):**
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

### Example 7: Audio extraction (async mode with webhook)

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

**Response (async - returned immediately):**
```json
{
  "task_id": "abc123-def456",
  "status": "processing",
  "message": "Task created and processing in background",
  "check_status_url": "http://video-processor:5001/task_status/abc123-def456"
}
```

**Note (v1.1.0):** `check_status_url` is now always a full URL (including scheme and host), ready for use in n8n and other systems.

**Check task status:**
```bash
curl http://localhost:5001/task_status/abc123-def456
```

**Response (when ready):**
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

**Webhook payload (sent automatically on completion):**
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

### Example 8: Video cutting + audio extraction (pipeline)

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

**Supported audio formats:**
- `mp3` (codec: libmp3lame) - universal format
- `aac` (codec: aac) - for Apple devices

**extract_audio parameters:**
- `format` (optional): `mp3` (default) or `aac`
- `bitrate` (optional): `128k`, `192k` (default), `256k`, `320k`
- `chunk_duration_minutes` (optional): Chunk duration in minutes for splitting large files
- `max_chunk_size_mb` (optional): Maximum chunk size in MB (default: 24 for Whisper API)
- `optimize_for_whisper` (optional): `true` - optimization for Whisper API (16kHz, mono, 64k bitrate)

Note: When splitting is enabled (via `chunk_duration_minutes` or `max_chunk_size_mb`), each object in `output_files` additionally contains only one field:
- `chunk`: compact chunk index in `i:n` format (e.g., `"1:7"`)

### Example 9: Audio extraction with automatic chunking for Whisper API

**Problem:** Whisper API doesn't accept files larger than 25 MB.

**Solution:** Automatic splitting into chunks < 24 MB.

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

**Webhook payload (when ready):**
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

**Files available at the following URLs:**
```
/download/xyz123/audio_20251112_194523_chunk000.mp3  (23.5 MB, 0:00 - 15:30)
/download/xyz123/audio_20251112_194523_chunk001.mp3  (23.2 MB, 15:30 - 31:00)
/download/xyz123/audio_20251112_194523_chunk002.mp3  (18.1 MB, 31:00 - 45:00)
/download/xyz123/metadata.json  (metadata for all files)
```

**How to download all chunks:**
```bash
# All chunks available by pattern
curl http://localhost:5001/download/xyz123/audio_20251112_194523_chunk000.mp3 -o chunk000.mp3
curl http://localhost:5001/download/xyz123/audio_20251112_194523_chunk001.mp3 -o chunk001.mp3
curl http://localhost:5001/download/xyz123/audio_20251112_194523_chunk002.mp3 -o chunk002.mp3
```

**Chunk fields in responses:**
- `chunk`: current chunk index and total count in `i:n` format

### Example 10: Manual chunk duration setting

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

Will create chunks of 10 minutes each, optimized for Whisper API (16kHz, mono, 64k bitrate).

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

Hint: to parse `chunk`, split the string by `:` → `i` and `n`.

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
  - /path/to/fonts:/app/fonts/custom   # Custom fonts
```

**Task directory structure:**
```
/app/tasks/{task_id}/
  ├── input_*.mp4       # Input files (deleted after processing)
  ├── temp_*.mp4        # Temporary files (deleted after processing)
  ├── short_*.mp4       # Completed Shorts videos (TTL: 2 hours)
  ├── video_*.mp4       # Completed cut videos (TTL: 2 hours)
  ├── audio_*.mp3       # Extracted audio tracks (TTL: 2 hours)
  └── metadata.json    # Metadata for all files
```

---

## 📝 File Retention

- **Task directories**: Automatically deleted after **2 hours** from creation
- **Input/Temp files**: Files with `input_*` and `temp_*` prefixes are deleted immediately after processing completion
- **Output files**: Files with `short_*`, `video_*`, `audio_*` prefixes are stored for 2 hours in `/app/tasks/{task_id}/`
- **Redis Tasks**: TTL = 24 hours
- **Metadata.json**: Stored for 2 hours and used as fallback for `/task_status` when task is not in Redis/memory **(v1.1.0)**

---

## 🛠 Development

## 💡 Client Integration Tips

- `output_files`: always an array. Even for a single file, use iteration.
- `is_chunked`: determine batch processing by this flag and/or presence of `chunk`.
- `chunk` format: string `"i:n"`, where `i` — 1-based index, `n` — total number of parts.
- `client_meta`: pass arbitrary JSON in request — it will be returned as-is in responses, webhooks, and `metadata.json`.
- Download links: use `download_url` for public access and `download_path` for internal calls via API gateway.
- Metadata: `metadata_url` contains full result snapshot — convenient for caching.
- Webhooks: handle both events — `task_completed` and `task_failed`.
- TTL: files are stored for 2 hours; download/move to permanent storage immediately after `completed`.
- **Input URLs** **(v1.1.0)**: Pass direct links to media files, not to HTML pages. API automatically checks Content-Type and rejects invalid files with clear errors.
- **Full URLs** **(v1.1.0)**: All URLs in responses (`check_status_url`, `download_url`, `metadata_url`) are now absolute, ready for use in n8n and external systems.
- **404 protection** **(v1.1.0)**: Endpoint `/task_status` uses filesystem fallback — even if task is absent in Redis/memory, status will be read from `metadata.json`.

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

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

## 📧 Contact

- GitHub: [@alexbic](https://github.com/alexbic)
- Issues: [GitHub Issues](https://github.com/alexbic/video-processor-api/issues)

