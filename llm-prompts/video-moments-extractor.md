# LLM Prompt: Video Moments Extractor for Shorts

Этот промпт используется для анализа видео и выделения вирусных моментов для TikTok/Instagram Reels/YouTube Shorts с автоматической генерацией субтитров.

## Промпт для LLM

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

## n8n Integration

### 1. Подготовка данных для LLM (Code Node)

После получения результатов от Whisper API:

```javascript
// Whisper API вернул массив words с абсолютными таймкодами
const whisperWords = $json.words; // [{word: "привет", start: 0.5, end: 1.2}, ...]
const transcriptText = $json.text;

// Конвертируем в формат для LLM (короткие ключи для экономии токенов)
const words_llm = whisperWords.map(w => ({
  w: w.word,
  s: w.start,
  e: w.end
}));

return [{
  json: {
    video_duration: $json.duration,
    text_llm: transcriptText,
    words_llm: words_llm,
    source_video_url: $json.source_video_url
  }
}];
```

### 2. Обработка ответа LLM (Code Node)

После получения JSON от LLM:

```javascript
// Обрабатываем ответ от LLM и подготавливаем для Video Processor API
const response = $json;
const shorts = response.shorts || [];

// Настройки текстовых оверлеев
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
  fontcolor: "#90EE90",  // светло-зеленый
  bordercolor: "white",
  borderw: 3,
  y: "h-150"  // 150 пикселей от низа
};

// Подготавливаем массив запросов для Video Processor API
const requests = shorts.map((short, index) => ({
  video_url: response.source_video_url,
  start_time: short.start,
  end_time: short.end,
  crop_mode: "letterbox",  // горизонтальное видео с размытым фоном
  title_text: short.title,
  subtitles: short.subtitles,
  title_config: title_config,
  subtitle_config: subtitle_config,

  // Метаданные для последующей публикации
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

## Полный n8n Workflow

```
1. [YouTube Downloader API]
   ↓ download_url, video_duration

2. [Video Processor: Extract Audio]
   POST /extract_audio
   ↓ audio file(s) - автоматически чанки если > 25MB

3. [IF: Check mode]
   → single: один файл
   → chunked: несколько чанков

4. [Whisper API]
   POST https://api.openai.com/v1/audio/transcriptions
   Body:
   - file: audio (binary)
   - model: whisper-1
   - language: ru
   - timestamp_granularities: ["word"]
   - response_format: verbose_json
   ↓ {text, words: [{word, start, end}], duration}

5. [Code: Prepare for LLM]
   → Конвертировать в формат {w, s, e}
   → Добавить video_duration, source_video_url

6. [LLM: Google Gemini / OpenAI GPT]
   → Использовать промпт выше
   ↓ JSON: {source_video_url, shorts: [...]}

7. [Code: Prepare for Video API]
   → Добавить title_config, subtitle_config
   → Подготовить metadata

8. [HTTP: POST /process_to_shorts_async]
   URL: http://video-processor:5001/process_to_shorts_async
   Method: POST
   Body: JSON from previous step
   → Запустить ВСЕ клипы параллельно
   ↓ task_ids массив

9. [Loop: Check Status]
   → [Wait 5 seconds]
   → [HTTP: GET /task_status/{task_id}]
   → [IF: все completed?]
      ✅ Да → продолжить
      ❌ Нет → loop обратно к Wait

10. [HTTP: Download Shorts]
    GET {download_url}
    Response Format: File
    ↓ готовые видео с субтитрами и заголовками

11. [Upload to Platforms]
    → TikTok: используем metadata.tiktok_description
    → Instagram: используем metadata.instagram_description
    → YouTube: используем metadata.youtube_title
```

## Пример итогового запроса к Video Processor API

```json
{
  "video_url": "http://youtube_downloader:5000/download_file/video_20240115.mp4",
  "start_time": 125.340,
  "end_time": 165.900,
  "crop_mode": "letterbox",
  "title_text": "Эпичный трюк!",
  "subtitles": [
    {"text": "Смотрите что", "start": 0.000, "end": 1.200},
    {"text": "я сейчас сделаю", "start": 1.250, "end": 2.500},
    {"text": "это будет нереально", "start": 2.600, "end": 4.800},
    {"text": "приготовьтесь", "start": 5.000, "end": 6.500}
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
}
```

## Настройка стилей субтитров

### Цветовые схемы

```javascript
// Светло-зеленый (по умолчанию)
{ "fontcolor": "#90EE90", "bordercolor": "white" }

// Желтый (популярный в TikTok)
{ "fontcolor": "yellow", "bordercolor": "black" }

// Белый классический
{ "fontcolor": "white", "bordercolor": "black" }

// Неоновый розовый
{ "fontcolor": "#FF69B4", "bordercolor": "white" }

// Голубой
{ "fontcolor": "#00BFFF", "bordercolor": "white" }
```

### Позиционирование

```javascript
// Внизу экрана (по умолчанию)
{ "y": "h-150" }

// Выше от низа
{ "y": "h-200" }

// По центру экрана
{ "y": "(h-text_h)/2" }

// Вверху (под title)
{ "y": "200" }
```

### Размеры шрифта

```javascript
// Крупный (для коротких фраз)
{ "fontsize": 56 }

// Средний (по умолчанию)
{ "fontsize": 48 }

// Мелкий (для длинных фраз)
{ "fontsize": 42 }
```

## Tips & Best Practices

### Для LLM агента:
1. **Выбирайте яркие моменты** - неожиданные повороты, смешные ситуации, полезные советы
2. **Группируйте слова в фразы** - не делайте субтитры пословно, объединяйте в смысловые группы (2-6 слов)
3. **Используйте естественные паузы** - начинайте/заканчивайте клипы на паузах в речи
4. **Короткие заголовки** - 3-5 слов, цепляющие, с эмоцией
5. **Описания с хештегами** - добавляйте релевантные хештеги для каждой платформы

### Для субтитров:
1. **Не перегружайте экран** - максимум 2 строки текста одновременно
2. **Синхронизация критична** - убедитесь что timestamps точные (относительные от начала клипа!)
3. **Читабельность** - используйте контрастные цвета (светлый текст + темная обводка или наоборот)
4. **Длительность сегмента** - 1-3 секунды оптимально для чтения

### Для заголовков:
1. **Fade-эффекты** - делают появление плавным и профессиональным
2. **Короткая длительность** - 3-5 секунд достаточно, не перекрывайте основной контент
3. **Позиция** - вверху (y=100) чтобы не конфликтовать с субтитрами внизу

## Troubleshooting

### Проблема: Субтитры не синхронны с речью
**Решение**: Проверьте что LLM правильно конвертирует абсолютные таймкоды в относительные (вычитает clip.start)

### Проблема: Слишком много текста на экране
**Решение**: Уменьшите количество слов в фразе (2-4 слова) или уменьшите fontsize

### Проблема: Субтитры не видны на светлом фоне
**Решение**: Увеличьте borderw до 4-5 или используйте более темную bordercolor

### Проблема: Title перекрывает важный контент
**Решение**: Измените y позицию или сократите duration заголовка

## Changelog

- **2025-01-15**: Создан промпт с поддержкой динамических субтитров и letterbox mode
- **2025-01-15**: Добавлены примеры n8n интеграции и настройки стилей
