# Video Processor API — Release Notes v1.2.0 (2025-11-15)

## 🚀 Highlights
- Flat task storage layout finalized (no `output/` segment in download paths)
- Operation names unified (breaking): `cut` → `cut_video`, `to_shorts` → `make_short`
- Manual recovery endpoint added (optional, disabled by default)
- Async tasks now persist initial `metadata.json` on creation (better recovery)
- Docs overhaul (EN/RU): modes, environment tables, absolute URLs, security notes

## 🔥 Breaking Changes
- Download paths:
  - Old: `/download/{task_id}/output/{filename}`
  - New: `/download/{task_id}/{filename}`
- Operations:
  - `cut` → `cut_video`
  - `to_shorts` → `make_short`

Please update your n8n workflows and any client code.

## ✨ New
- `GET/POST /recover/{task_id}` — manual recovery by task id
  - Controlled by `RECOVERY_PUBLIC_ENABLED` (default: `false`)
  - Optional `force=1` to ignore TTL expiry
- Initial metadata persisted for async tasks to disk at creation time
- Extended startup logs (recovery config + public recover endpoint status)

## 🛡️ Stability
- Recovery on startup scans `/app/tasks` and re-runs stuck tasks within TTL
- Periodic recovery available via `RECOVERY_INTERVAL_MINUTES > 0`
- Input validation for media (headers/signatures/min size) before FFmpeg
- Absolute URLs for `check_status_url` and background-generated links

## ⚙️ Env Vars (additions)
- `INTERNAL_BASE_URL` — base for background absolute URLs (default: `http://video-processor:5001`)
- `RECOVERY_PUBLIC_ENABLED` — enable public `/recover/{task_id}` (default: `false`)

## 🧹 Repo & DX
- `.gitignore` ignores local test mounts (`.tasks-test/`) and `docker-compose.*.test.yml`
- Example compose kept as `docker-compose.redis-example.yml`

## ✅ Tested
- Redis-backed multi-worker (2 workers): async and sync flows
- Manual recover (with/without `force`) → completed task
- `/task_status` filesystem fallback works after restarts

---
Thanks for using Video Processor API! 🙌
