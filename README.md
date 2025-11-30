# Video Processor API

**Open Source** REST API for video processing with FFmpeg. Create vertical Shorts, add subtitles, cut videos, extract audio.

[![Docker Hub](https://img.shields.io/docker/v/alexbic/video-processor-api?label=Docker%20Hub&logo=docker)](https://hub.docker.com/r/alexbic/video-processor-api)
[![GitHub](https://img.shields.io/badge/GitHub-alexbic/video--processor--api-blue?logo=github)](https://github.com/alexbic/video-processor-api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](docs/RELEASE_NOTES_v1.0.0.md)

**English** | [Русский](README.ru.md)

---

## ✨ Features

- 🎬 **Pipeline Processing** - chain multiple operations sequentially (cut → make_short → extract_audio)
- 📦 **Letterbox Mode** - convert horizontal videos to vertical format (1080x1920) with blurred background
- 📝 **Universal Text Items System** - flexible text overlays with individual timing, positioning, and styling
- 🎨 **Dynamic Subtitles** - word-level timing with custom fonts, colors, background boxes, and positioning
- 🖼️ **Auto Thumbnails** - automatic JPEG thumbnail generation from processed videos (perfect for YouTube/TikTok)
- ✂️ **Video Cutting** - precise cutting by timecodes with automatic Shorts conversion
- 🎵 **Audio Extraction** - with automatic chunking for Whisper API (max 24MB per chunk)
- 📡 **Webhooks** - completion notifications with exponential backoff retry and background resender (every 15 min)
- 🎯 **Custom Webhook Headers** - per-request authentication headers for webhook security
- 🔄 **Webhook State Tracking** - unified webhook state in metadata.json with delivery status
- ⏰ **File Expiration Tracking** - `expires_at` field shows exact deletion time (ISO 8601)
- ⚡ **Async Processing** - background processing with real-time status tracking
- 🔠 **10 Tested Fonts** - built-in fonts with full Cyrillic support (public version)
- 🐳 **Built-in Redis** - embedded Redis server (256MB, localhost:6379) for task management
- 🛡️ **Input Validation** - automatic media file validation before processing (Content-Type, signatures, size)
- 🔗 **Smart URL Generation** - absolute URLs in all responses (public/internal modes)
- 🧹 **Smart Cleanup** - orphaned tasks deleted after 1h, expired tasks after 3 days (hardcoded)
- 🔄 **Automatic Recovery** - scans and retries stuck tasks on startup (max 3 retries)
- 📦 **Client Metadata** - pass-through custom JSON data (max 16KB) for platform-specific content

---

## 🚀 Quick Start

### Docker Run (Production Ready)

```bash
docker pull alexbic/video-processor-api:latest
docker run -d -p 5001:5001 \
  -v $(pwd)/tasks:/app/tasks \
  --name video-processor \
  alexbic/video-processor-api:latest
```

**Public version includes:**
- ✅ Built-in Redis (256MB, localhost:6379)
- ✅ 2 Gunicorn workers (hardcoded)
- ✅ Automatic task cleanup (every hour)
- ✅ 3-day file retention (hardcoded)

### Docker Compose (Optional)

```bash
docker-compose up -d
```

**Configuration:**
- Port: 5001:5001
- Volume: `./tasks:/app/tasks` (task storage)

---

## 📚 API Reference

### 🔐 Authentication

API supports **smart dual-mode operation** with Bearer token authentication:

**🔑 Two Operation Modes:**

1️⃣ **Public API Mode** (when BOTH `API_KEY` AND `PUBLIC_BASE_URL` are set):
   - Protected endpoints require Bearer token authentication
   - Download URLs use public domain from `PUBLIC_BASE_URL`
   - Recommended for production with reverse proxy/CDN
   - Both parameters must be configured together

2️⃣ **Internal Docker Network Mode** (when `API_KEY` or `PUBLIC_BASE_URL` is NOT set):
   - All endpoints work without authentication
   - API operates within Docker network (e.g., with n8n)
   - Download URLs use internal Docker hostnames (`http://video-processor:5001`)
   - Ideal for trusted internal services
   - Works when: neither parameter set, only `API_KEY` set, or only `PUBLIC_BASE_URL` set

**Setup:**
```bash
# Generate secure API key
openssl rand -hex 32

# Public API mode (requires authentication) - BOTH parameters required
export API_KEY="your-generated-key-here"
export PUBLIC_BASE_URL="https://your-domain.com/video-api"

# Internal Docker mode (no authentication) - unset both or either
unset API_KEY
unset PUBLIC_BASE_URL
```

**Usage with API Key:**
```bash
curl -H "Authorization: Bearer your-api-key" \
  -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{"video_url": "...", "operations": [...]}'
```

**Endpoint Protection:**
- ✅ **Always public**: `/health`, `/fonts`, `/task_status/{task_id}`, `/download/{task_id}/...`
- 🔒 **Protected in Public mode** (when both `API_KEY` and `PUBLIC_BASE_URL` are set): `/process_video`, `/tasks`
- 🔐 **Task access**: `task_id` acts as temporary access token (UUID, 72h TTL)

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
- `GET /fonts` — list of available fonts (10 fonts in public version) **[no authorization]**
- `POST /process_video` — make_short, cut_video, extract_audio (sync/async, webhooks) **[requires API key in Public mode only]**
- `GET /task_status/{task_id}` — task status (`queued`/`processing`/`completed`/`error`) **[no authorization]**
- `GET /tasks` — recent tasks (for debugging) **[requires API key in Public mode only]**
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
  "fonts": [
    {
      "name": "Charter",
      "filename": "Charter.ttc",
      "file": "/app/fonts/Charter.ttc",
      "type": "ttc"
    },
    {
      "name": "Copperplate",
      "filename": "Copperplate.ttc",
      "file": "/app/fonts/Copperplate.ttc",
      "type": "ttc"
    },
    ...
  ],
  "note": "These are the custom fonts available for video generation in /app/fonts/"
}
```

**Available Fonts (Public Version):**
- 10 built-in fonts with full Cyrillic support
- Use `GET /fonts` to see the complete list
- Custom fonts available in Pro Edition only

See [FONTS.md](docs/FONTS.md) for font details and examples.

---

### Video Processing

`POST /process_video`

**Request structure:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "sync|async",
  "operations": [{"type": "make_short|cut_video|extract_audio", ...}],
  "webhook": {"url": "...", "headers": {...}},
  "client_meta": {...}
}
```

**Available operations:**
- `cut_video` - cut video by timecodes
- `make_short` - convert to Shorts format with text overlays (max 2 text items in public version)
- `extract_audio` - extract audio track with automatic chunking for Whisper API

See [📖 Examples](#-examples) section below for detailed usage examples.

---

### Response Format

**Unified format** - all operations return the same structure:

```json
{
  "task_id": "abc123",
  "status": "completed",
  "created_at": "2025-01-08T10:05:18",
  "completed_at": "2025-01-08T10:05:23",
  "input": {
    "video_url": "https://example.com/video.mp4",
    "operations": [
      {
        "operation": "make_short",
        "title": "Amazing Video",
        "font": "Montserrat-Bold.ttf"
      }
    ],
    "operations_count": 1
  },
  "output": {
    "output_files": [
      {
        "filename": "short_20251116_210049.mp4",
        "file_size": 16040960,
        "file_size_mb": 15.3,
        "download_url": "http://video-processor:5001/download/abc123/short_20251116_210049.mp4",
        "download_path": "/download/abc123/short_20251116_210049.mp4"
      },
      {
        "filename": "short_20251116_210049_thumbnail.jpg",
        "file_size": 211762,
        "file_size_mb": 0.2,
        "download_url": "http://video-processor:5001/download/abc123/short_20251116_210049_thumbnail.jpg",
        "download_path": "/download/abc123/short_20251116_210049_thumbnail.jpg"
      }
    ],
    "total_files": 2,
    "total_size": 16252722,
    "total_size_mb": 15.5,
    "is_chunked": false,
    "metadata_url": "/download/abc123/metadata.json",
    "ttl_seconds": 259200,
    "ttl_human": "3 days",
    "expires_at": "2025-01-11T10:05:23"
  }
}
```

**Response structure:**
- Top level: `task_id`, `status`, timestamps
- `input`: Original request data (`video_url`, `operations`)
- `output`: Processing results (`output_files`, `total_files`, metadata URL, TTL info)
- `output_files` is **always an array** (even if 1 file)
- `is_chunked`: `true` if files are split into chunks (for Whisper API)

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
  "created_at": "2025-01-08T10:05:18",
  "completed_at": "2025-01-08T10:05:23",
  "input": {
    "video_url": "https://example.com/video.mp4",
    "operations": [{"operation": "cut_video", "start": 10, "end": 30}],
    "operations_count": 1
  },
  "output": {
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
    "ttl_seconds": 259200,
    "ttl_human": "3 days",
    "expires_at": "2025-01-11T10:05:23"
  }
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
  "created_at": "2025-01-08T10:05:18",
  "completed_at": "2025-01-08T10:05:23",
  "input": {
    "video_url": "https://example.com/video.mp4",
    "operations": [{"operation": "cut_video", "start": 10, "end": 30}]
  },
  "output": {
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
    "ttl_seconds": 259200,
    "ttl_human": "3 days",
    "expires_at": "2025-01-11T10:05:23"
  }
}
```

---

### Webhooks

Add `webhook` object to receive notifications on task completion:

```json
{
  "webhook": {
    "url": "https://n8n.example.com/webhook/video-completed"
  }
}
```

**Custom Webhook Headers (Optional):**

You can add custom headers for webhook authentication via `webhook.headers`:

```json
{
  "webhook": {
    "url": "https://n8n.example.com/webhook/video-completed",
    "headers": {
      "X-API-Key": "your-secret-key",
      "Authorization": "Bearer token-123"
    }
  }
}
```

**Use Cases:**
- 🔑 Different API keys for different webhooks
- 🎫 Request-specific authorization tokens
- 🏷️ Custom tracing/correlation IDs
- 👤 Client identification headers

**Validation:**
- Must be JSON object with string keys/values
- Header name max: 256 chars
- Header value max: 2048 chars
- `Content-Type` cannot be overridden
- Specify `webhook.headers` in each request (global headers not supported in public version)

---

**Webhook Payload (success):**
```json
{
  "task_id": "abc123",
  "event": "task_completed",
  "status": "completed",
  "created_at": "2025-01-08T10:05:18",
  "completed_at": "2025-01-08T10:05:23",
  "input": {
    "video_url": "https://example.com/video.mp4",
    "operations": [{"operation": "cut_video", "start": 10, "end": 30}],
    "operations_count": 1
  },
  "output": {
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
    "ttl_seconds": 259200,
    "ttl_human": "3 days",
    "expires_at": "2025-01-11T10:05:23"
  }
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

**Webhook State Tracking:**

Webhook delivery state is saved in `metadata.json` under `webhook` field:

```json
{
  "webhook": {
    "url": "https://n8n.example.com/webhook/video-completed",
    "headers": {"X-API-Key": "***"},
    "status": "delivered",
    "attempts": 1,
    "last_attempt": "2025-01-08T10:05:23",
    "last_status": 200,
    "last_error": null,
    "next_retry": null
  }
}
```

**Retry Logic:**
- Initial attempts: 3 tries with exponential backoff (5s, 15s, 1m)
- **Background Resender**: Automatically retries failed webhooks every 15 minutes
- Retry delays: 5min → 15min → 1h → 4h → 12h → 24h (max)
- Webhook status: `pending` → `delivered` / `failed`
- Failed webhooks continue retrying until delivered or task TTL expires (3 days)

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
| **Authentication & URLs** |||
| `API_KEY` | — | Enables public mode (Bearer required). When unset, internal mode (no auth). |
| `PUBLIC_BASE_URL` | — | External base for absolute URLs (https://host/app). Used only if `API_KEY` is set. |
| `INTERNAL_BASE_URL` | `http://video-processor:5001` | Base for background URL generation (webhooks, logs). |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). |

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

### Example 1: Shorts with automatic cutting and text overlays

**What it does:**
- Cuts video from 10.5 to 70 seconds (59.5 sec total)
- Converts horizontal to vertical (1080x1920) with blurred background
- Adds title text (stays 60 sec) with semi-transparent black box
- Adds call-to-action text (shows first 3 sec only)
- Auto-generates JPEG thumbnail

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
      "text_items": [
        {
          "text": "My First Shorts",
          "fontfile": "HelveticaNeue.ttc",
          "fontsize": 70,
          "fontcolor": "white",
          "x": "(w-text_w)/2",
          "y": 100,
          "start": 0,
          "end": 60,
          "box": 1,
          "boxcolor": "black@0.5"
        },
        {
          "text": "Subscribe for more!",
          "fontfile": "PTSans.ttc",
          "fontsize": 48,
          "fontcolor": "yellow",
          "x": "(w-text_w)/2",
          "y": "h-200",
          "start": 0,
          "end": 3
        }
      ],
      "generate_thumbnail": true
    }
  ]
}
```

**Note:** `start_time`/`end_time` accept numbers (seconds) or strings (`"00:01:30"`). Time in `text_items` is relative to the cropped video.

### Example 2: Simple Shorts conversion (letterbox only, no text)

**What it does:**
- Converts horizontal video to vertical format (letterbox mode)
- No text overlays - clean conversion only
- Generates thumbnail from frame at 0.5 seconds

```json
{
  "video_url": "https://example.com/landscape.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "make_short",
      "crop_mode": "letterbox",
      "generate_thumbnail": true,
      "thumbnail_timestamp": 0.5
    }
  ]
}
```

### Example 3: Dynamic subtitles with word-level timing

**What it does:**
- Static title at top (stays entire duration) with background box
- Dynamic subtitles at bottom with word-level timing
- Each word appears/disappears at specific time (karaoke-style)
- Text outline (`borderw`: 3px black) + background box with 8px border
- Inherits style from container: all words use same font, size, colors

```json
{
  "video_url": "https://example.com/video.mp4",
  "execution": "sync",
  "operations": [
    {
      "type": "make_short",
      "crop_mode": "letterbox",
      "text_items": [
        {
          "text": "Title",
          "fontfile": "HelveticaNeue.ttc",
          "fontsize": 80,
          "fontcolor": "white",
          "x": "(w-text_w)/2",
          "y": 100,
          "start": 0,
          "end": 60,
          "box": 1,
          "boxcolor": "black@0.5"
        },
        {
          "text": "",
          "fontfile": "PTSans.ttc",
          "fontsize": 60,
          "fontcolor": "yellow",
          "borderw": 3,
          "bordercolor": "black",
          "box": 1,
          "boxcolor": "black@0.7",
          "boxborderw": 8,
          "x": "(w-text_w)/2",
          "y": "h-200",
          "subtitles": {
            "items": [
              {"text": "First word", "start": 0, "end": 1.5},
              {"text": "Second word", "start": 1.5, "end": 3},
              {"text": "Third word", "start": 3, "end": 4.5}
            ]
          }
        }
      ]
    }
  ]
}
```

### Example 4: Video cutting

**What it does:**
- Cuts video from 1:30 to 2:00 (30 seconds total)
- No format conversion - preserves original aspect ratio
- Supports both formats: numbers (seconds) or strings ("HH:MM:SS")

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

**What it does:**
- **Step 1:** Cut video from 10 sec to 1 min (50 sec total)
- **Step 2:** Convert cut video to Shorts with title
- Operations execute sequentially - output of step 1 feeds into step 2
- Async mode - returns immediately with task_id for status checking

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
  "note": "Files will auto-delete after 3 days.",
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
  "webhook": {
      "url": "https://n8n.example.com/webhook/audio-ready"
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
  "file_ttl_seconds": 259200,
  "file_ttl_human": "3 days",
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
  "webhook": {
      "url": "https://n8n.example.com/webhook/audio-extracted"
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
  "webhook": {
      "url": "https://n8n.example.com/webhook/audio-chunks-ready"
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
  "file_ttl_seconds": 259200,
  "file_ttl_human": "3 days",
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

## ⚙️ Configuration

### Environment Variables (Public Version)

**Configurable Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `None` | Bearer token for authentication. If set, enables Public API mode with protected endpoints. If not set, runs in Internal mode without authentication. |
| `PUBLIC_BASE_URL` | `None` | External base URL for download links (e.g., `https://domain.com/api`). Only used when `API_KEY` is set. Ignored in Internal mode. |
| `INTERNAL_BASE_URL` | `http://video-processor:5001` | Internal Docker network URL for background tasks. Used when generating URLs in webhooks/metadata without request context. |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). |

**Hardcoded Parameters (Public Version):**

The following parameters are **hardcoded** in the public version. They can be configured in the Pro Edition.

| Parameter | Public Value | Pro Edition |
|-----------|--------------|-------------|
| `TASK_TTL_HOURS` | 72 (3 days) | 1-720 hours configurable |
| `WORKERS` | 2 | 1-10+ configurable |
| `REDIS_HOST` | `localhost` | External Redis support |
| `REDIS_PORT` | 6379 | Configurable |
| `REDIS_MAXMEMORY` | 256MB | Unlimited with external Redis |
| `CLEANUP_INTERVAL_SECONDS` | 3600 (1 hour) | Configurable |
| `WEBHOOK_BACKGROUND_INTERVAL_SECONDS` | 900 (15 min) | Configurable |
| `MAX_TASK_RETRIES` | 3 | Configurable |
| `RETRY_DELAY_SECONDS` | 60 | Configurable |
| `MAX_CLIENT_META_BYTES` | 16384 (16 KB) | Configurable |
| `MAX_CLIENT_META_DEPTH` | 5 | Configurable |
| `MAX_CLIENT_META_KEYS` | 200 | Configurable |
| `MAX_TEXT_ITEMS_PER_OPERATION` | 2 | 10 in Pro Edition |

**Upgrade to Pro:** support@alexbic.net

### Docker Volumes

**Public Version:**
```yaml
volumes:
  - /path/to/tasks:/app/tasks          # Task-based storage (files + metadata.json)
```

**Pro Edition:**
```yaml
volumes:
  - /path/to/tasks:/app/tasks          # Task-based storage (files + metadata.json)
  - /path/to/fonts:/app/fonts/custom   # Custom fonts (Pro Edition only)
```

**Task directory structure:**
```
/app/tasks/{task_id}/
  ├── input_*.mp4       # Input files (deleted after processing)
  ├── temp_*.mp4        # Temporary files (deleted after processing)
  ├── short_*.mp4       # Completed Shorts videos (TTL: 3 days)
  ├── video_*.mp4       # Completed cut videos (TTL: 3 days)
  ├── audio_*.mp3       # Extracted audio tracks (TTL: 3 days)
  └── metadata.json    # Metadata for all files
```

---

## 📝 File Retention

- **Task directories**: Automatically deleted after **3 days** (72 hours) from creation (hardcoded in public version)
- **Orphaned tasks**: Tasks without `metadata.json` are deleted after **1 hour**
- **Input/Temp files**: Files with `input_*` and `temp_*` prefixes are deleted immediately after processing completion
- **Output files**: Files with `short_*`, `video_*`, `audio_*` prefixes are stored for 3 days in `/app/tasks/{task_id}/`
- **Redis Tasks**: TTL = 24 hours
- **Metadata.json**: Stored for 3 days and used as fallback for `/task_status` when task is not in Redis/memory
- **File Expiration**: `expires_at` field in metadata.json shows exact deletion time (ISO 8601 format)

**Cleanup Behavior:**
- **Expired tasks**: Deleted when `expires_at` < current time (logged with size)
- **Orphaned tasks**: Deleted after 1 hour if no metadata.json found
- **Background cleanup**: Runs every hour automatically
- **Detailed logging**: Shows task ID, size freed (MB), and deletion reason

**Why 3 days?** This TTL provides enough time to upload processed videos to YouTube, TikTok, and other platforms without rushing.

---

## 🔍 Troubleshooting

### Common Issues

#### 1. FFmpeg errors with input files

**Problem:** `Invalid data found when processing input` or `moov atom not found`

**Solutions:**
- Ensure `video_url` points directly to a media file, not an HTML page
- API validates Content-Type automatically (rejects `text/html`, `application/json`)
- Minimum file size: 100 KB
- Supported formats: MP4, WebM, MPEG-TS

#### 2. Redis connection issues

**Problem:** `Could not connect to Redis`

**Solutions:**
- Public version uses built-in Redis (localhost:6379)
- Verify supervisor properly started Redis
- API automatically falls back to memory mode if Redis is unavailable
- Check logs: Redis should start automatically with container

#### 3. Files not found after completion

**Problem:** `404 File not found` when downloading

**Solutions:**
- Files auto-delete after 3 days (configurable via `TASK_TTL_HOURS`)
- Check task status first: `GET /task_status/{task_id}`
- Download immediately after `status: "completed"`
- Use `metadata.json` for file inventory

#### 4. Webhook not received

**Problem:** Webhook payload not arriving

**Solutions:**
- Check webhook URL is accessible from container
- API retries 3 times with exponential backoff (1s, 2s, 4s)
- Check container logs: `docker logs video-processor`
- Verify webhook endpoint accepts POST requests

#### 5. Task stuck in "processing" state

**Problem:** Task never completes or fails

**Solutions:**
- Check recovery settings: `RECOVERY_ENABLED=true` (default)
- Manual recovery: `GET /recover/{task_id}` (requires `RECOVERY_PUBLIC_ENABLED=true`)
- Check container logs for FFmpeg errors
- Verify video file is accessible and valid

#### 6. Authentication errors

**Problem:** `401 Unauthorized` or `Invalid API key`

**Solutions:**
- If `API_KEY` is set, all protected endpoints require `Authorization: Bearer <key>`
- Protected endpoints: `/process_video`, `/tasks`, `/fonts`
- Public endpoints (no auth): `/health`, `/task_status`, `/download`
- If using internal Docker mode, unset `API_KEY` entirely

#### 7. Download URLs not working externally

**Problem:** URLs work internally but not from external systems

**Solutions:**
- Set `PUBLIC_BASE_URL` to your external domain (e.g., `https://domain.com/api`)
- Requires `API_KEY` to be set (public mode)
- Without `API_KEY`, `PUBLIC_BASE_URL` is ignored (internal mode)
- Verify reverse proxy/CDN configuration

#### 8. Font not found

**Problem:** Font not available in public version

**Solutions:**
- Public version includes 10 built-in fonts only
- Use `GET /fonts` to see available fonts
- Pro Edition supports custom fonts via volume mount
- See [FONTS.md](docs/FONTS.md) for font list and examples

#### 9. Client metadata validation errors

**Problem:** `client_meta validation failed` or `client_meta too large`

**Solutions:**
- Max size: 16 KB (JSON UTF-8)
- Max depth: 5 levels
- Max keys: 200 total
- Max string length: 1000 characters
- Max list length: 200 items
- Use flat structure when possible

#### 10. Task status returns 404

**Problem:** `Task not found` for valid task_id

**Solutions:**
- Redis tasks expire after 24 hours
- API uses filesystem fallback (reads `metadata.json`)
- Task directories deleted after 3 days (files + metadata)
- Check `/app/tasks/{task_id}/` directory exists

### Logging

**View container logs:**
```bash
# Real-time logs
docker logs -f video-processor

# Last 100 lines
docker logs --tail 100 video-processor

# Logs with timestamps
docker logs -t video-processor
```

**Common log patterns:**
- `[INFO] Task {task_id} created` - Task started
- `[INFO] Task {task_id} completed` - Task finished successfully
- `[ERROR] FFmpeg error:` - Video processing error
- `[WARNING] Webhook failed:` - Webhook delivery issue
- `[INFO] Recovery started` - Automatic recovery triggered

### Health Check

**Verify service status:**
```bash
curl http://localhost:5001/health
```

**Healthy response:**
```json
{
  "status": "healthy",
  "service": "video-processor-api",
  "storage_mode": "redis",
  "redis_available": true,
  "api_key_enabled": true,
  "timestamp": "2025-11-16T10:00:00"
}
```

**What to check:**
- `status` should be `"healthy"`
- `storage_mode`: `"redis"` (preferred) or `"memory"` (fallback)
- `redis_available`: `true` for multi-worker support
- `api_key_enabled`: matches your configuration

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
- TTL: files are stored for 3 days; download/move to permanent storage immediately after `completed`.
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

