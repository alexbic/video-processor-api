# Video Processor API — Release Notes v1.2.0 (2025-11-16)

**Open Source Video Processing API with FFmpeg** - Major stability and documentation update.

---

## 🚀 Highlights

### Core Improvements
- ✅ **Flat task storage layout** - simplified download paths (no `output/` segment)
- ✅ **Unified operation names** - consistent API naming convention
- ✅ **Manual recovery endpoint** - optional public recovery with safety controls
- ✅ **Enhanced async reliability** - initial metadata persistence on task creation
- ✅ **Comprehensive documentation** - complete troubleshooting guide, all env vars documented

### Documentation Overhaul
- 📚 **Complete environment variables table** - all 20 variables documented with categories
- 🔍 **Troubleshooting section** - 10 common issues with solutions
- 🌐 **Bilingual support** - EN/RU fully synchronized
- 📄 **MIT License** - proper open-source licensing
- 📖 **Updated examples** - all code samples verified for v1.2.0

---

## 🔥 Breaking Changes

### ⚠️ Action Required

#### 1. Download Path Structure
**Old format:**
```
/download/{task_id}/output/{filename}
```

**New format:**
```
/download/{task_id}/{filename}
```

**Impact:** All download URLs have changed. Update your n8n workflows, scripts, and client code.

**Migration example:**
```bash
# Old
curl http://localhost:5001/download/abc123/output/video.mp4

# New
curl http://localhost:5001/download/abc123/video.mp4
```

#### 2. Operation Names
**Renamed operations:**
- `cut` → `cut_video`
- `to_shorts` → `make_short`

**Impact:** All API requests must use new operation names.

**Migration example:**
```json
{
  "operations": [
    {"type": "cut_video", "start_time": 10, "end_time": 60},
    {"type": "make_short", "crop_mode": "letterbox"}
  ]
}
```

**Note:** Old operation names (`cut`, `to_shorts`) are **not supported** in v1.2.0+

---

## ✨ New Features

### 1. Manual Recovery Endpoint
**Endpoint:** `GET/POST /recover/{task_id}`

Manually trigger recovery for stuck or failed tasks:
```bash
# Basic recovery
curl http://localhost:5001/recover/abc123

# Force recovery (ignore TTL expiry)
curl http://localhost:5001/recover/abc123?force=1
```

**Configuration:**
- Controlled by `RECOVERY_PUBLIC_ENABLED` (default: `false`)
- Disabled by default for security
- Optional `force=1` parameter to ignore TTL expiry
- Returns task status and retry count

**Security note:** Enable only in trusted networks. Use reverse proxy authentication if exposing publicly.

### 2. Initial Metadata Persistence
**Async tasks now create `metadata.json` immediately on task creation:**
- Better recovery reliability
- Task status available even after Redis restart
- Filesystem fallback for `/task_status` endpoint

**Before:** metadata.json created only after task completion
**After:** metadata.json created at task creation + updated on completion

### 3. Enhanced Startup Logging
**Detailed service configuration on startup:**
```
[INFO] Storage mode: redis
[INFO] Redis available: True
[INFO] API key enabled: True
[INFO] Recovery enabled: True
[INFO] Recovery interval: 0 minutes (startup only)
[INFO] Public recovery endpoint: Disabled
```

---

## 🛡️ Stability & Reliability

### Automatic Recovery System
- **Startup recovery:** Scans `/app/tasks` for stuck tasks within TTL
- **Periodic recovery:** Optional via `RECOVERY_INTERVAL_MINUTES > 0`
- **Smart retries:** Max 3 retries with 60s delay (configurable)
- **TTL enforcement:** Only recovers tasks within 2-hour TTL window

### Input Validation
**Pre-processing validation prevents FFmpeg errors:**
- Content-Type checking (rejects `text/html`, `application/json`)
- File signature analysis (MP4, WebM, MPEG-TS magic bytes)
- Minimum file size threshold (100 KB)
- Clear error messages instead of cryptic FFmpeg output

### Absolute URLs Everywhere
**All URLs now absolute for external integrations:**
- `check_status_url` in async responses
- `download_url` in all responses and webhooks
- `metadata_url` in task status and webhooks
- Works correctly in webhook/background contexts

---

## ⚙️ Environment Variables

### New Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `INTERNAL_BASE_URL` | `http://video-processor:5001` | Base URL for background task URL generation |
| `RECOVERY_PUBLIC_ENABLED` | `false` | Enable public `/recover/{task_id}` endpoint |

### Complete List (20 Total)
All environment variables now fully documented in README with categories:
- **Authentication & URLs** (3 vars)
- **Worker Configuration** (1 var)
- **Redis Configuration** (3 vars)
- **Task Management** (1 var)
- **Recovery System** (5 vars)
- **Client Metadata Limits** (6 vars)

See README.md for complete table.

---

## 📚 Documentation Updates

### New Sections
1. **🔍 Troubleshooting**
   - 10 common issues with solutions
   - FFmpeg errors, Redis issues, webhooks, authentication
   - Logging guide with docker commands
   - Health check verification

2. **⚙️ Complete Environment Variables Table**
   - All 20 variables documented
   - Organized by category
   - Clear descriptions and defaults

3. **📄 MIT License**
   - Added LICENSE file
   - Proper open-source licensing
   - Resolves broken documentation links

### Updated Sections
- **API Reference:** Verified all endpoints and examples
- **Examples:** All 10 examples updated for v1.2.0
- **Configuration:** Complete env var documentation
- **Client Integration Tips:** Extended with new features

### Bilingual Support
- **English:** README.md (100% complete)
- **Russian:** README.ru.md (100% synchronized)
- Identical structure and content across both languages

---

## 🧹 Repository & Developer Experience

### File Organization
```
/app/tasks/{task_id}/
  ├── input_*.mp4       # Temp input files (auto-deleted)
  ├── temp_*.mp4        # Temp processing files (auto-deleted)
  ├── short_*.mp4       # Shorts output (2h TTL)
  ├── video_*.mp4       # Cut video output (2h TTL)
  ├── audio_*.mp3       # Audio output (2h TTL)
  └── metadata.json     # Task metadata (2h TTL)
```

### Semantic File Prefixes
- `input_*` - Input files from video_url (deleted after processing)
- `temp_*` - Intermediate processing files (deleted after processing)
- `short_*` - Shorts operation output (retained 2h)
- `video_*` - Cut operation output (retained 2h)
- `audio_*` - Audio extraction output (retained 2h)

### .gitignore Updates
- Ignores local test mounts (`.tasks-test/`)
- Ignores test docker-compose files (`docker-compose.*.test.yml`)
- Example compose kept as `docker-compose.redis-example.yml`

---

## ✅ Testing & Validation

### Tested Scenarios
- ✅ Redis-backed multi-worker (2 workers): async and sync flows
- ✅ Manual recovery with/without `force` parameter
- ✅ `/task_status` filesystem fallback after Redis restart
- ✅ Input validation (HTML pages, invalid formats, small files)
- ✅ Absolute URLs in webhook payloads
- ✅ All 10 code examples in documentation
- ✅ Both English and Russian documentation

### Platform Testing
- Docker: `python:3.11-slim` base image
- Multi-arch: `amd64`, `arm64` (via GitHub Actions)
- Redis: v5.0.1 (optional, memory fallback available)

---

## 🔄 Migration Guide

### From v1.1.0 to v1.2.0

#### Step 1: Update API Requests
```json
{
  "operations": [
    {"type": "cut_video"},      // Changed from "cut"
    {"type": "make_short"}      // Changed from "to_shorts"
  ]
}
```

#### Step 2: Update Download URLs
**If hardcoded in your code:**
```javascript
// Old
const url = `${base}/download/${taskId}/output/${filename}`

// New
const url = `${base}/download/${taskId}/${filename}`
```

**If using response URLs (recommended):**
No changes needed - use `download_url` from API responses.

#### Step 3: Review Environment Variables
**New optional variables:**
- `INTERNAL_BASE_URL` - set if using custom internal networking
- `RECOVERY_PUBLIC_ENABLED` - set to `true` if you need public recovery endpoint

**All other variables:** No changes required, backward compatible.

#### Step 4: Test Workflows
1. Test async task creation and status polling
2. Verify webhook payloads
3. Check download URL accessibility
4. Validate error handling

---

## 🐛 Bug Fixes

- **Fixed:** Duplicate startup logs with multiple workers
- **Fixed:** Broken LICENSE link in README
- **Fixed:** Missing environment variables in documentation
- **Fixed:** Inconsistent URL formats in webhook context
- **Fixed:** Task status 404 after Redis restart (filesystem fallback)

---

## 📊 Statistics

**Documentation:**
- Lines added: ~350+
- Environment variables documented: 20/20 (100%)
- Code examples: 10 (all verified)
- Troubleshooting issues covered: 10
- Languages: 2 (EN/RU, fully synchronized)

**Code Quality:**
- Input validation: Content-Type + file signature + size checks
- URL consistency: All absolute URLs
- Recovery reliability: Filesystem fallback + retry logic
- Error messages: Clear, actionable descriptions

---

## 🔗 Resources

- **GitHub Repository:** https://github.com/alexbic/video-processor-api
- **Docker Hub:** https://hub.docker.com/r/alexbic/video-processor-api
- **Documentation:** README.md (English) | README.ru.md (Russian)
- **License:** MIT License (see LICENSE file)
- **Issues:** https://github.com/alexbic/video-processor-api/issues

---

## 🎯 Next Steps

After upgrading to v1.2.0:

1. ✅ Update your API client code with new operation names
2. ✅ Update download URL construction (if hardcoded)
3. ✅ Review new environment variables
4. ✅ Test recovery functionality
5. ✅ Check troubleshooting guide for optimization tips

---

## 🙏 Acknowledgments

Special thanks to all contributors and users who provided feedback for this release.

**Full Changelog:** https://github.com/alexbic/video-processor-api/compare/v1.1.0...v1.2.0

---

**Thanks for using Video Processor API!** 🎬✨

Questions? Open an issue on GitHub or check the comprehensive troubleshooting guide in README.md.
