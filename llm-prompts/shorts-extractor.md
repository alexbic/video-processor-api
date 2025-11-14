# LLM Prompt: Video Moments Extractor

Промпт для LLM (Gemini/GPT) для автоматического выделения вирусных моментов из видео с генерацией субтитров.

## Промпт

```
You are a senior short-form video editor. Read the ENTIRE transcription and word-level timestamps to pick the 3–15 MOST VIRAL moments for TikTok/IG Reels/YouTube Shorts. Each clip must be 15–60 seconds.

For each selected clip, you MUST:
- Assign a "virality_score" (float, 7.5–10.0, e.g. 9.5) predicting how viral this moment will be as a Short (10.0 = maximum viral potential).
- Add a "virality_reason" (1–3 sentences, in English, explaining why this moment is likely to go viral: e.g. emotional impact, humor, twist, relatability, etc.).
- Do NOT return any clips with a virality_score below 7.5.

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

⚠️ OUTPUT FORMAT - CRITICAL:
- Return PURE JSON ONLY (start with { and end with })
- NO ```json markdown blocks
- NO explanatory text before or after
- NO comments inside JSON
Order clips by predicted performance (best first):
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
      ,"virality_score": <float, e.g. 9.5>,
      "virality_reason": "<short explanation in English>"
    }
  ]
}

EXAMPLE SUBTITLE CONVERSION:
If clip.start = 100.0 and word in WORDS_JSON is {"w": "привет", "s": 100.5, "e": 101.2}
Then in subtitles array: {"text": "привет", "start": 0.5, "end": 1.2}

⚠️ CRITICAL: Subtitles timestamps MUST be relative to clip start (subtract clip.start from all word timestamps).
```

---

## Промпт (Русская версия)

```
Ты старший редактор коротких видео. Прочитай ВЕСЬ текст транскрипции и таймкоды на уровне слов, чтобы выбрать 3-15 САМЫХ ВИРУСНЫХ моментов для TikTok/IG Reels/YouTube Shorts. Каждый клип должен быть 15-60 секунд.

Для каждого выбранного клипа:
- Обязательно добавь поле "virality_score" (оценка вирусности, число с плавающей точкой от 7.5 до 10.0, например 9.5), отражающее насколько этот момент потенциально вирусный (10.0 = максимум).
- Обязательно добавь поле "virality_reason" (1–3 предложения по-русски, почему этот момент может стать вирусным: эмоции, юмор, неожиданный поворот, узнаваемость и т.д.).
- Не возвращай клипы с оценкой ниже 7.5.

⚠️ ЖЁСТКИЕ ТРЕБОВАНИЯ ПО ТАЙМКОДАМ ДЛЯ FFMPEG:
- Возвращай таймкоды как АБСОЛЮТНЫЕ СЕКУНДЫ от начала видео (для использования в: ffmpeg -ss <start> -to <end> -i <input> …).
- ТОЛЬКО ЧИСЛА с десятичной ТОЧКОЙ, до 3 знаков после запятой (примеры: 0, 1.250, 17.350).
- Убедись что 0 ≤ start < end ≤ VIDEO_DURATION_SECONDS.
- Каждый клип от 15 до 60 секунд включительно.
- Предпочитай начинать на 0.2-0.4с РАНЬШЕ хука и заканчивать на 0.2-0.4с ПОСЛЕ кульминации.
- Используй паузы для естественных переходов; никогда не режь посреди слова или фразы.
- СТРОГО никаких форматов времени кроме абсолютных секунд.

ДЛИТЕЛЬНОСТЬ_ВИДЕО_СЕКУНД: {{ $json.video_duration }}

ТЕКСТ_ТРАНСКРИПЦИИ (сырой):
{{ JSON.stringify($json.text_llm) }}

МАССИВ_СЛОВ (массив объектов {w, s, e} где s/e - секунды):
{{ JSON.stringify($json.words_llm) }}

ИСКЛЮЧЕНИЯ:
- Никаких общих интро/аутро или только рекламных сегментов, если только они не содержат хук.
- Никаких клипов < 15с или > 60с.

📝 ТРЕБОВАНИЯ К СУБТИТРАМ:
- Для каждого клипа извлеки субтитры на уровне слов из МАССИВ_СЛОВ.
- Преобразуй абсолютные таймкоды в ОТНОСИТЕЛЬНЫЕ (локальные для клипа):
  * relative_start = word.s - clip.start
  * relative_end = word.e - clip.start
- Группируй слова в КОРОТКИЕ фразы (максимум 2-6 слов) для лучшей читаемости.
- Каждый сегмент субтитров должен быть 1-3 секунды для оптимального просмотра.
- Используй естественные границы фраз (запятые, паузы, конец предложения).
- ⚠️ ВАЖНО: таймкоды должны быть ОТНОСИТЕЛЬНЫМИ от начала клипа (начинаются с 0).

⚠️ ФОРМАТ ВЫВОДА - КРИТИЧНО:
- Верни ТОЛЬКО чистый JSON (начинается с { и заканчивается })
- БЕЗ markdown блоков ```json
- БЕЗ пояснительного текста до или после
- БЕЗ комментариев внутри JSON
Сортируй клипы по предсказанной виральности (лучшие первыми):
{
  "source_video_url": "{{ $json.source_video_url }}",
  "shorts": [
    {
      "start": <число секунд от начала видео, например 12.340>,
      "end": <число секунд от начала видео, например 37.900>,
      "title": "<короткий цепляющий заголовок для клипа (3-5 слов)>",
      "subtitles": [
        {"text": "Привет всем", "start": 0.000, "end": 1.250},
        {"text": "сегодня покажу", "start": 1.300, "end": 2.500},
        {"text": "как сделать крутые Shorts", "start": 2.600, "end": 5.100}
      ],
      "video_description_for_tiktok": "<описание для TikTok на русском с хэштегами для получения просмотров>",
      "video_description_for_instagram": "<описание для Instagram на русском с эмодзи для получения просмотров>",
      "video_title_for_youtube_short": "<заголовок для YouTube Shorts на русском для получения просмотров>"
      ,"virality_score": <float, например 9.5>,
      "virality_reason": "<короткое объяснение по-русски>"
    }
  ]
}

ПРИМЕР КОНВЕРТАЦИИ СУБТИТРОВ:
Если clip.start = 100.0 и слово в МАССИВ_СЛОВ это {"w": "привет", "s": 100.5, "e": 101.2}
Тогда в массиве subtitles: {"text": "привет", "start": 0.5, "end": 1.2}

⚠️ КРИТИЧНО: Таймкоды субтитров ДОЛЖНЫ быть относительными от начала клипа (вычитай clip.start из всех таймкодов слов).
```

---

## n8n Code Nodes

### Code Node 1: Prepare Whisper data for LLM

```javascript
// Input: items из Whisper API с {text, words, duration, source_video_url}
return items.map(item => {
  const dur = Number(item.json.duration || 0);

  // Округление до 3 знаков (важно для LLM!)
  const round3 = (n) => Math.round(Number(n) * 1000) / 1000;

  // Whisper возвращает words при timestamp_granularities: "word"
  const wordsLLM = (item.json.words || []).map(w => ({
    w: w.word,
    s: round3(w.start),
    e: round3(w.end),
  }));

  // Формируем данные для LLM
  item.json.video_duration = round3(dur);
  item.json.words_llm = wordsLLM;
  item.json.text_llm = item.json.text;
  item.json.source_video_url = item.json.source_video_url;

  return item;
});
```

### Code Node 2: Extract JSON from LLM (если вернул markdown)

```javascript
// LLM иногда возвращает JSON в markdown блоке ```json...```
// Этот node извлекает чистый JSON
let output = $json.output || JSON.stringify($json);

// Убираем markdown блоки
output = output.replace(/```json\n?/g, '').replace(/```\n?$/g, '').trim();

// Парсим JSON
const parsed = JSON.parse(output);

return [{json: parsed}];
```

### Code Node 3: Process LLM response

```javascript
const response = $json;
const shorts = response.shorts || [];

const title_config = {
  fontsize: 60,
  fontcolor: "white",
  bordercolor: "black",
  borderw: 3,
  y: 200,  // Опущено ниже для баланса композиции
  start_time: 0.5,
  duration: 4,
  fade_in: 0.5,
  fade_out: 0.5
};

const subtitle_config = {
  fontsize: 64,  // Увеличен для лучшей читаемости на TikTok/Shorts
  fontcolor: "#90EE90",
  bordercolor: "white",
  borderw: 4,  // Увеличена обводка для контрастности
  y: "h-300"  // Поднято выше для баланса композиции
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

## Text Wrapping (Перенос текста)

API автоматически переносит длинный текст заголовков и субтитров на 2 строки:
- Расчёт: `max_chars_per_line = 950 / (fontsize * 0.55)`
- Для `fontsize: 64` → ~12 символов на строку (субтитры)
- Для `fontsize: 60` → ~14 символов на строку (заголовок)
- Для `fontsize: 48` → ~16 символов на строку
- Максимум 2 строки одновременно
- Используется `expansion=normal` в FFmpeg drawtext для поддержки `\n`

**Пример:**
```
Текст: "Это очень длинная фраза для субтитров"
Результат (fontsize 64):
Это очень
длинная фраза
```

**Работает для:**
- ✅ Заголовка (title_text)
- ✅ Субтитров (subtitles[].text)

## Troubleshooting

**Субтитры не синхронны** → LLM должен вычесть `clip.start` из всех таймкодов
**Слишком много текста** → Уменьшите слова в фразе (2-4 слова) или `fontsize`
**Текст обрезается** → API автоматически переносит, но лучше короче фразы (2-4 слова)
**Плохая контрастность** → Увеличьте `borderw` до 4-5
