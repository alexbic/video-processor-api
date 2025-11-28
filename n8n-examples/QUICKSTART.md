# Quick Start Guide (3 Steps)

## Step 1: Copy AI Prompt

Open [prompts/shorts-extractor.md](prompts/shorts-extractor.md) and copy **entire content** to your N8N AI Agent node.

**AI Agent settings:**
```
Model: gemini-2.0-flash-exp
Max Output Tokens: 8192
Temperature: 0.7
```

---

## Step 2: Add Code Node for Response Parsing

Create Code Node after AI Agent and paste code from [code-nodes/parse-ai-response.js](code-nodes/parse-ai-response.js)

---

## Step 3: Send Input Data

**For short videos (< 30 min):**
```json
{
  "text_llm": "full video transcription...",
  "words_llm": [{w: "word", s: 123.5, e: 124.0}, ...],
  "video_duration": 1800,
  "language": "ru",
  "client_meta": {}
}
```

**Done!** AI will return viral shorts with platform-specific content.

---

## Optional: Block Processing for Long Videos (1+ hour)

Add 2 more code nodes BEFORE AI Agent:

1. **Split Into Blocks** - [code-nodes/split-into-blocks.js](code-nodes/split-into-blocks.js)
2. **Loop Over Items** (N8N native, batch=1, sequential)
3. AI Agent (same as above)
4. Parse Response (same as above)
5. **Deduplicate** - [code-nodes/deduplicate-shorts.js](code-nodes/deduplicate-shorts.js)

**Input data with blocks:**
```json
{
  "text_llm": "...",
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

## Output Example

```json
{
  "shorts": [
    {
      "start": 123.5,
      "end": 178.2,
      "title": "Epic Moment",
      "subtitles": [...],
      "client_meta": {
        "youtube_title": "...",
        "tiktok_title": "...",
        "instagram_description": "...",
        "virality_score": 9.5
      }
    }
  ]
}
```

---

**Need more details?** See [README.md](README.md)
