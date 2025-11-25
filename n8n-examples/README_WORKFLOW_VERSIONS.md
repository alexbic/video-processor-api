# Gaming Templates v4.0 - Two Versions

## Overview
Two workflow implementations for N8n with Gaming Templates v4.0 supporting the Video Processor API.

### 📁 Files
- **`workflow-code-v4.js`** - NEW: Title with atomic breakdown
- **`workflow-code-v4-LEGACY.js`** - OLD: Title as-is (without breakdown)

---

## Key Differences

### workflow-code-v4.js (NEW VERSION)
✨ **Features:**
- Title is processed and broken down into **separate atoms** if it contains multiple lines
- Each atom becomes its own `text_item` with individual styling
- Ideal for **multilevel titles** and complex text layouts
- Maximum 2 text_items on input, unlimited after expansion
- Subtitles array is also expanded into separate text_items

**Example:**
```javascript
// Input Title: "Main\nTitle"
// Output: 2 separate text_items (one for "Main", one for "Title")
```

**Use this when you want:**
- Complex multi-line titles
- Each line to have independent positioning
- Better control over text hierarchy
- Dynamic subtitle expansion with parameter inheritance

---

### workflow-code-v4-LEGACY.js (OLD VERSION)
📦 **Features:**
- Title is passed **as-is** without any breakdown
- Subtitles array is **combined into single text_item** (all lines joined with newlines)
- Simple, straightforward implementation
- Perfect for simple use cases with unified subtitle blocks

**Example:**
```javascript
// Input Subtitles: ["Line 1", "Line 2", "Line 3"]
// Output: 1 text_item with text = "Line 1\nLine 2\nLine 3"
```

**Use this when you want:**
- Simple, single-line titles
- Subtitles combined as one text block
- No complex text layering
- Backwards compatibility with old workflows
- Minimal text processing

---

## 30 Gaming Templates

Both versions include the same **30 gaming templates** organized in 3 categories:

### 1️⃣ GAMING_CONTRAST (10 templates)
High-contrast color schemes for maximum impact:
- cyber_neon, fire_ice, gold_purple, toxic_green, electric_yellow
- blood_shadow, matrix_code, royal_blue, lava_glow, cosmic_purple

### 2️⃣ DOUBLE_BOX (10 templates)
Both title and subtitle with background boxes:
- double_neon, double_impact, double_elegant, double_toxic, double_gold
- double_cyber, double_fire, double_ice, double_purple, double_clean

### 3️⃣ NO_BOX (10 templates)
Text with outline only, no background:
- outline_neon, outline_fire, outline_classic, outline_rainbow, outline_gold
- outline_toxic, outline_blood, outline_ice, outline_purple, outline_contrast

---

## Public Version Fonts (10)

All templates use only these system fonts available in the public version:

1. **Charter.ttc** - Modern Serif
2. **Copperplate.ttc** - Decorative style
3. **HelveticaNeue.ttc** - Premium Sans-Serif
4. **LucidaGrande.ttc** - Elegant Sans-Serif
5. **MarkerFelt.ttc** - Creative style
6. **Menlo.ttc** - Monospace
7. **Monaco.ttf** - Monospace
8. **PTSans.ttc** - Russian font
9. **Palatino.ttc** - Classic Serif
10. **STIXTwoText-Italic.ttf** - Scientific (Math)

---

## Input Format

### Data Structure
```json
{
  "source_video_url": "file:///path/to/video.mp4",
  "shorts": {
    "title": "Main Title",
    "subtitles": [
      { "text": "Sub 1", "start": 0, "end": 2 },
      { "text": "Sub 2", "start": 2, "end": 5 }
    ],
    "start": 0,
    "end": 10,
    "client_meta": {
      "template_name": "cyber_neon",  // or
      "template_category": "GAMING_CONTRAST",  // or
      "template_genre": "cyberpunk"
    }
  }
}
```

### Template Selection Priority
1. **Exact template name** → `template_name: "cyber_neon"`
2. **Category** → `template_category: "GAMING_CONTRAST"`
3. **Genre** → `template_genre: "cyberpunk"` (filters by `best_for`)
4. **Random** → If none specified, random template from all 30

---

## Output Format (API Request)

Both versions generate this API request format:

```json
{
  "video_url": "file:///path/to/video.mp4",
  "execution": "async",
  "operations": [{
    "type": "make_short",
    "start_time": 0,
    "end_time": 10,
    "crop_mode": "letterbox",
    "letterbox_config": { "blur_radius": 20 },
    "text_items": [
      {
        "text": "Main Title",
        "fontfile": "/app/fonts/PTSans.ttc",
        "fontsize": 75,
        "fontcolor": "#FF00FF",
        ...
      },
      {
        "text": "Sub 1",
        "fontfile": "/app/fonts/PTSans.ttc",
        "fontsize": 60,
        "fontcolor": "#FF00FF",
        "start": 0,
        "end": 2
      },
      ...
    ],
    "generate_thumbnail": true,
    "thumbnail_timestamp": 0.5
  }],
  "client_meta": {
    "_template_key": "cyber_neon",
    "_template_name": "Cyber Neon",
    "_template_category": "GAMING_CONTRAST",
    "_template_genres": ["cyberpunk", "tech", "sci-fi"]
  }
}
```

---

## Comparison Table

| Feature | v4.js (NEW) | v4-LEGACY.js |
|---------|-------------|--------------|
| **Title** | As-is (no breakdown) | As-is (no breakdown) |
| **Subtitles** | Expanded into separate text_items | Combined into single text_item |
| **Max Input Items** | 2 (before expansion) | 2 (no expansion) |
| **Use Case** | Complex multi-subtitle scenes | Simple unified subtitle block |
| **Styling per Subtitle** | ✅ Individual control | ❌ Shared styling |
| **Timing per Subtitle** | ✅ Precise timing | ⏱️ First/Last timing only |

### Input Format Comparison

```javascript
// Input: Same for both
const shorts = {
  title: "Main Title",
  subtitles: [
    { text: "Line 1", start: 0, end: 2 },
    { text: "Line 2", start: 2, end: 4 },
    { text: "Line 3", start: 4, end: 5 }
  ]
};

// v4.js OUTPUT (NEW): 4 text_items
// [
//   { text: "Main Title" },
//   { text: "Line 1", start: 0, end: 2 },
//   { text: "Line 2", start: 2, end: 4 },
//   { text: "Line 3", start: 4, end: 5 }
// ]

// v4-LEGACY.js OUTPUT: 2 text_items
// [
//   { text: "Main Title" },
//   { text: "Line 1\nLine 2\nLine 3", start: 0, end: 5 }
// ]
```

---

---

## Testing

Both versions have been tested with:
- ✅ Local file:// URLs
- ✅ Subtitle expansion with timing
- ✅ Parameter inheritance (fontsize, fontcolor, box, etc)
- ✅ 2-item input limit enforcement
- ✅ All 30 templates
- ✅ Random template selection

---

## Notes

- **Max 2 text_items on input** (public version limitation)
- Unlimited after expansion via subtitle arrays
- Full parameter inheritance: fonts, colors, boxes, positioning
- Per-item overrides supported via `sub.get(param, parent.get(param))`
- Supports `file://` URLs with bind mount volumes in Docker
