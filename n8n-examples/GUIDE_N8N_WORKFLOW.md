# N8N Workflow for Video Shorts Extraction

Extract viral moments from long videos and generate platform-specific content for YouTube Shorts, TikTok, and Instagram Reels.

---

## 🚀 Quick Start

### 1. Copy System Prompt

Use **[prompts/shorts-extractor.md](prompts/shorts-extractor.md)** in your N8N AI Agent node (Gemini/OpenAI/Claude).

**Model settings:**
- Model: `gemini-2.0-flash-exp`
- Max Output Tokens: `8192` (critical!)
- Temperature: `0.7`

### 2. Add Code Nodes

Copy code from `code-nodes/` directory:

**For long videos (1+ hour) with block processing:**
1. [split-into-blocks.js](code-nodes/split-into-blocks.js) → Split video into blocks
2. [parse-ai-response.js](code-nodes/parse-ai-response.js) → Parse AI response
3. [deduplicate-shorts.js](code-nodes/deduplicate-shorts.js) → Remove duplicates

**For short videos (< 30 min):**
- Only [parse-ai-response.js](code-nodes/parse-ai-response.js)

### 3. Configure Input

**Without blocks (short videos):**
```json
{
  "text_llm": "full transcription...",
  "words_llm": [{w: "word", s: 123.5, e: 124.0}, ...],
  "video_duration": 1800,
  "language": "ru",
  "client_meta": {}
}
```

**With blocks (long videos):**
```json
{
  "block_id": 1,
  "total_blocks": 3,
  "main_zone_start": 0,
  "main_zone_end": 1800,
  "block_start": 0,
  "block_end": 1890,
  "text_llm": "block transcription...",
  "words_llm": [...],
  "video_duration": 5400,
  "language": "ru",
  "client_meta": {
    "max_blocks": 3,
    "overlap_seconds": 90
  }
}
```

---

## 📂 File Structure

```
n8n-examples/
├── README.md                    ← You are here
├── prompts/
│   └── shorts-extractor.md     ← Main AI prompt (v4.0)
├── code-nodes/
│   ├── split-into-blocks.js    ← Block splitting logic
│   ├── parse-ai-response.js    ← Parse AI JSON response
│   └── deduplicate-shorts.js   ← Remove duplicate shorts
├── guides/
│   ├── PLATFORM_CONTENT_GUIDE.md      ← Detailed platform guide
│   └── PLATFORM_QUICK_REFERENCE.md    ← Quick reference
└── archive/
    └── ...old files...
```

---

## 🎯 Workflow Schemas

### Simple Workflow (Short Videos < 30 min)

```
Whisper API
  ↓
Parse Whisper Results
  ↓
AI Agent (shorts-extractor.md)
  ↓
Parse AI Response
  ↓
Final Output: {shorts: [...]}
```

### Block Processing Workflow (Long Videos 1+ hour)

```
Whisper API
  ↓
Parse Whisper Results
  ↓
Split Into Blocks
  ↓
Loop Over Items (sequential, batch=1)
  ↓
AI Agent (shorts-extractor.md)
  ↓
Parse AI Response
  ↓
Deduplicate Shorts
  ↓
Final Output: {shorts: [...]}
```

---

## 💡 Key Features

✅ **Universal prompt** - works with blocks and without blocks
✅ **Platform-specific** - YouTube Shorts, TikTok, Instagram Reels
✅ **Virality scoring** - only clips with score >= 7.5
✅ **Smart subtitles** - word-level timestamps, auto-grouped
✅ **Client meta enrichment** - preserves existing fields
✅ **FFmpeg-ready** - absolute timestamps in seconds

---

## 📊 Output Format

```json
{
  "shorts": [
    {
      "start": 123.5,
      "end": 178.2,
      "title": "Epic Moment",
      "subtitles": [
        {"text": "Hello everyone", "start": 0.0, "end": 1.2}
      ],
      "client_meta": {
        "youtube_title": "How I Did This in 30 Seconds | Epic #Shorts",
        "youtube_description": "...",
        "tiktok_title": "How I Did This in 30 Seconds",
        "tiktok_description": "...",
        "instagram_description": "...",
        "duration": "PT55S",
        "duration_ms": 54700,
        "virality_score": 9.5,
        "virality_reason": "..."
      }
    }
  ]
}
```

---

## 🔧 Configuration

### Block Processing Settings

In `client_meta`:
```json
{
  "max_blocks": 3,           // Max number of blocks (default: 3)
  "overlap_seconds": 90      // Overlap between blocks (default: 90)
}
```

**Recommended settings:**

| Video Length | max_blocks | Result |
|-------------|------------|--------|
| < 30 min | 1 | No blocks |
| 30-60 min | 2 | 2 blocks ~25 min |
| 60-120 min | 3 | 3 blocks ~30 min |
| 120-180 min | 4 | 4 blocks ~35 min |

---

## 📚 Additional Resources

- **Platform guides**: See [guides/](guides/) directory
- **Detailed setup**: Check [workflow-sequential-blocks-example.md](workflow-sequential-blocks-example.md)
- **Old versions**: See [archive/](archive/) directory

---

**Version:** 4.0
**Last updated:** 2025-11-27
