# LLM Prompt: Video Moments Extractor

Промпт для LLM (Gemini/GPT) для автоматического выделения вирусных моментов из видео с генерацией субтитров.

## Промпт

```
You are a senior short-form video editor. Read the ENTIRE transcription and word-level timestamps to pick the 3–15 MOST VIRAL moments for TikTok/IG Reels/YouTube Shorts. Each clip must be 15–60 seconds.

⚠️ FFMPEG TIMING CONTRACT — HARD REQUIREMENTS:
- Return timestamps as ABSOLUTE SECONDS from video start (usable in: ffmpeg -ss <start> -to <end> -i <input> …).
- Numbers ONLY with DOT decimal, up to 3 decimals (examples: 0, 1.250, 17.350).
- Ensure 0 ≤ start < end ≤ VIDEO_DURATION_SECONDS.
- Each clip 15–60s inclusive.
- Prefer starting 0.2–0.4s BEFORE the hook and ending 0.2–0.4s AFTER the payoff.
- Use silent moments for natural cuts; never cut mid-word or mid-phrase.
- STRICTLY NO time formats other than absolute seconds.

VIDEO_DURATION_SECONDS: {{ $json.video_duration }}

TRANSCRIPT_TEXT (raw):
{{ JSON.stringify($json.text_llm) }}

WORDS_JSON (array of {w, s, e} where s/e are seconds):
{{ JSON.stringify($json.words_llm) }}

HARD EXCLUSIONS:
- No generic intros/outros or sponsor-only segments unless they contain the hook.
- No clips < 15s or > 60s.

📝 SUBTITLES REQUIREMENTS:
- For each clip, extract word-level subtitles from WORDS_JSON.
- Convert absolute timestamps to RELATIVE (clip-local) timestamps:
  * relative_start = word.s - clip.start
  * relative_end = word.e - clip.start
- Group words into SHORT phrases (2-6 words max) for better readability.
- Each subtitle segment should be 1-3 seconds long for optimal viewing.
- Use natural phrase boundaries (commas, pauses, sentence breaks).
- IMPORTANT: timestamps must be RELATIVE to clip start (0-based).

OUTPUT — RETURN ONLY VALID JSON (no markdown, no comments). Order clips by predicted performance (best first):
{
  "source_video_url": "{{ $json.source_video_url }}",
  "shorts": [
    {
      "start": <number seconds from video start, e.g. 12.340>,
      "end": <number seconds from video start, e.g. 37.900>,
      "title": "<короткий цепляющий заголовок для клипа (3-5 слов)>",
      "subtitles": [
        {"text": "Привет всем", "start": 0.000, "end": 1.250},
        {"text": "сегодня покажу", "start": 1.300, "end": 2.500},
        {"text": "как сделать крутые Shorts", "start": 2.600, "end": 5.100}
      ],
      "video_description_for_tiktok": "<tiktok video russian description for get views>",
      "video_description_for_instagram": "<instagram video russian description for get views>",
      "video_title_for_youtube_short": "<youtube short video russian title for get views>"
    }
  ]
}

EXAMPLE SUBTITLE CONVERSION:
If clip.start = 100.0 and word in WORDS_JSON is {"w": "привет", "s": 100.5, "e": 101.2}
Then in subtitles array: {"text": "привет", "start": 0.5, "end": 1.2}

⚠️ CRITICAL: Subtitles timestamps MUST be relative to clip start (subtract clip.start from all word timestamps).
```

## n8n Code Nodes

### Code Node 1: Prepare Whisper data for LLM

```javascript
// После Whisper API
const words_llm = $json.words.map(w => ({w: w.word, s: w.start, e: w.end}));
return [{json: {
  video_duration: $json.duration,
  text_llm: $json.text,
  words_llm: words_llm,
  source_video_url: $json.source_video_url
}}];
```

### Code Node 2: Process LLM response

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

## Workflow

```
Whisper API
  ↓ words: [{word, start, end}]
Code Node 1 (prepare)
  ↓ {text_llm, words_llm, video_duration}
LLM (промпт выше)
  ↓ {shorts: [{start, end, title, subtitles}]}
Code Node 2 (process)
  ↓ готовые запросы для Video Processor API
HTTP: POST /process_to_shorts_async
  ↓ task_ids
Loop: Check Status
  ↓ download_urls
```

## Tips

**Для LLM:**
- Выбирайте яркие моменты с неожиданными поворотами
- Группируйте слова в фразы (2-6 слов)
- Используйте паузы в речи для начала/конца клипов
- Короткие заголовки (3-5 слов)

**Для субтитров:**
- Максимум 2 строки текста одновременно
- Timestamps ОТНОСИТЕЛЬНЫЕ от начала клипа (0-based)
- Контрастные цвета для читабельности
- Длительность сегмента 1-3 секунды

## Troubleshooting

**Субтитры не синхронны** → LLM должен вычесть `clip.start` из всех таймкодов
**Слишком много текста** → Уменьшите слова в фразе (2-4) или `fontsize` до 42
**Плохая контрастность** → Увеличьте `borderw` до 4-5
