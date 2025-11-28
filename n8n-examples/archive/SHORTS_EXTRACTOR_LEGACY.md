# LLM Prompt: Video Moments Extractor

Промпт для LLM (Gemini/GPT) для автоматического выделения вирусных моментов из видео с генерацией субтитров.

## Промпт

```
You are a senior short-form video editor. Read the ENTIRE transcription and word-level timestamps to pick the 3–15 MOST VIRAL moments for TikTok/IG Reels/YouTube Shorts. Each clip must be 15–60 seconds.

For each selected clip, you MUST:
- Assign a "virality_score" (float, 7.5–10.0, e.g. 9.5) predicting how viral this moment will be as a Short (10.0 = maximum viral potential).
- Add a "virality_reason" (1–3 sentences, in Russian, explaining why this moment is likely to go viral: e.g. emotional impact, humor, twist, relatability, etc.).
- Do NOT return any clips with a virality_score below 7.5.

📝 PLATFORM-SPECIFIC CONTENT GENERATION:

For each clip, create optimized content for three platforms: YouTube Shorts, TikTok, and Instagram Reels.
Follow platform-specific requirements from the PLATFORM_CONTENT_GUIDE.md guidelines.

🎬 YOUTUBE SHORTS:
- **Title** (youtube_title):
  * Length: 30-50 characters (max 100)
  * Style: informative, SEO-optimized
  * Keywords at the beginning (first 40 characters visible in interface)
  * First-person, no clickbait
  * MUST include #Shorts at the end
  * Example (in Russian): "Как я победил босса за 30 секунд | Лайфхак #Shorts"

- **Description** (youtube_description):
  * Extended information with keywords
  * 1-3 relevant hashtags
  * Specific facts and results
  * Example (in Russian): "Показываю секретную тактику которая помогла мне победить сложнейшего босса всего за 30 секунд. Работает в 90% случаев!\n\n#gaming #геймплей #лайфхак"

🎵 TIKTOK (⚠️ TikTok has TWO separate fields!):

- **Title** (tiktok_title):
  * Length: 20-40 characters
  * SEO and search: short title with keywords
  * What exactly is shown in the video
  * NO hashtags (hashtags only in description)
  * Example (in Russian): "Как победить босса за 30 секунд"

- **Description/Caption** (tiktok_description):
  * Length: 50-150 characters (optimal)
  * Hook in the first words to grab attention
  * MUST include CTA (Call-to-Action): "Save it!", "Do you do this too?", "Write in comments"
  * 3-5 relevant hashtags at the end
  * Trending + niche hashtags
  * First-person, direct and engaging tone
  * Example (in Russian): "Этот трюк сэкономил мне 2 часа попыток 😱 Сохрани чтобы не потерять! А ты знал этот секрет? Напиши в комментах 👇 #gaming #геймплей #лайфхак #тикток #босс"

📸 INSTAGRAM REELS:
- **Caption** (instagram_description):
  * Length: up to 150 characters (first 125 visible before "...more")
  * Emotional hook in the first 125 characters
  * 3-5 emojis for visual accent
  * First-person, personal story
  * Call-to-action: "Share with a friend", "Save for later"
  * 3-5 hashtags at the end
  * Aesthetic formatting with paragraphs
  * Example (in Russian): "Я не верил что это сработает 😱 Но этот трюк изменил всё! 🎮 Теперь я прохожу боссов в 10 раз быстрее ✨\n\nПопробуй сам и напиши что получилось 👇 Кто со мной?\n\n#gaming #геймплей #лайфхак #gamer #мотивация"

🔑 GENERAL RULES FOR ALL PLATFORMS:
- Write in first person (I, me, my experience)
- Use specific numbers and facts (30 seconds, 2 hours, 90%, 10 times)
- Emotional triggers: surprise, curiosity, motivation
- Hashtags ONLY relevant to content
- Do NOT invent game names — use only identifiable ones from the transcript
- If game is unclear — use neutral tags (#gaming #геймплей #gamer)

CLIENT_META PASS-THROUGH AND ENRICHMENT:
- If input data includes  $json.client_meta , preserve ALL existing fields inside it.
- Add the following NEW fields into client_meta for each clip:
  * "youtube_title" — YouTube Shorts title (30-50 chars, SEO, #Shorts at the end)
  * "youtube_description" — YouTube description (informative, keywords, 1-3 hashtags)
  * "tiktok_title" — TikTok title (20-40 chars, SEO, NO hashtags)
  * "tiktok_description" — TikTok description/caption (50-150 chars, hook + CTA + 3-5 hashtags)
  * "instagram_description" — Instagram caption (up to 150 chars, emotional hook + emojis + 3-5 hashtags)
  * "virality_score" — float (7.5–10.0)
  * "virality_reason" — short English explanation (1-3 sentences)
- Do NOT remove or overwrite any fields that were already in client_meta on input.
- Return the enriched client_meta object in each clip's JSON output.

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

CLIENT_META (input, may be empty or contain existing fields):
{{ JSON.stringify($json.client_meta || {}) }}

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
- ⚠️ CRITICAL: **The FIRST subtitle MUST start at 0.0** (start: 0.0), not with a delay!
  * Shift the start of the first subtitle to 0.0, BUT keep the end unchanged
  * This ensures text appears immediately, without a blank screen at the beginning
  * Example: if the first subtitle was {"text": "Hello", "start": 0.2, "end": 1.5}, change it to {"text": "Hello", "start": 0.0, "end": 1.5}

⚠️ OUTPUT FORMAT - CRITICAL:
- Return PURE JSON ONLY (start with { and end with })
- NO ```json markdown blocks
- NO explanatory text before or after
- NO comments inside JSON
Order clips by predicted virality (best first):
{
  "source_video_url": "{{ $json.client_meta.source.videoUrl }}",
  "shorts": [
    {
      "start": <number seconds from video start, e.g. 12.340>,
      "end": <number seconds from video start, e.g. 37.900>,
      "title": "<short catchy clip title (3-5 words in Russian)>",
      "subtitles": [
        {"text": "Привет всем", "start": 0.000, "end": 1.250},
        {"text": "сегодня покажу", "start": 1.300, "end": 2.500},
        {"text": "как сделать крутые Shorts", "start": 2.600, "end": 5.100}
      ],
      "client_meta": {
        ...existing fields from input client_meta (if any)...,
        "youtube_title": "<YouTube Shorts title in Russian, 30-50 chars, #Shorts at the end>",
        "youtube_description": "<YouTube description in Russian with keywords, 1-3 hashtags>",
        "tiktok_title": "<TikTok title in Russian, 20-40 chars, NO hashtags>",
        "tiktok_description": "<TikTok description in Russian, 50-150 chars, hook + CTA + 3-5 hashtags>",
        "instagram_description": "<Instagram caption in Russian, up to 150 chars, emotional hook + emojis + 3-5 hashtags>",
        "duration": <<end>-<start> ISO 8601 duration format, e.g. PT1M39S>,
        "duration_ms": <number miliseconds <end>-<start>, e.g. 99000>,
        "virality_score": <float, e.g. 9.5>,
        "virality_reason": "<short explanation in Russian, 1-3 sentences>"
      }
    }
  ]
}

EXAMPLE SUBTITLE CONVERSION:
If clip.start = 100.0 and word in WORDS_JSON is {"w": "привет", "s": 100.5, "e": 101.2}
Then in subtitles array: {"text": "привет", "start": 0.5, "end": 1.2}

EXAMPLE CLIENT_META ENRICHMENT:
Input client_meta: {"user_id": "abc123", "campaign": "winter2025"}
Output client_meta for a clip: {"user_id": "abc123", "campaign": "winter2025", "youtube_title": "...", "youtube_description": "...", "tiktok_title": "...", "tiktok_description": "...", "instagram_description": "...","duration":"PT1M39S", "duration_ms":"99000", "virality_score": 9.2, "virality_reason": "..."}

⚠️ CRITICAL: 
- Subtitles timestamps MUST be relative to clip start (subtract clip.start from all word timestamps).
- Preserve ALL incoming client_meta fields and add new ones; do NOT replace the entire object.
```

---

## Промпт (Русская версия)

```
Ты старший редактор коротких видео. Прочитай ВЕСЬ текст транскрипции и таймкоды на уровне слов, чтобы выбрать 3-15 САМЫХ ВИРУСНЫХ моментов для TikTok/IG Reels/YouTube Shorts. Каждый клип должен быть 15-60 секунд.

Для каждого выбранного клипа:
- Обязательно добавь поле "virality_score" (оценка вирусности, число с плавающей точкой от 7.5 до 10.0, например 9.5), отражающее насколько этот момент потенциально вирусный (10.0 = максимум).
- Обязательно добавь поле "virality_reason" (1–3 предложения по-русски, почему этот момент может стать вирусным: эмоции, юмор, неожиданный поворот, узнаваемость и т.д.).
- Не возвращай клипы с оценкой ниже 7.5.

📝 ГЕНЕРАЦИЯ ПЛАТФОРМО-СПЕЦИФИЧНОГО КОНТЕНТА:

Для каждого клипа создай оптимизированный контент для трёх платформ: YouTube Shorts, TikTok и Instagram Reels.
Следуй платформо-специфичным требованиям из руководства PLATFORM_CONTENT_GUIDE.md.

🎬 YOUTUBE SHORTS:
- **Заголовок** (youtube_title):
  * Длина: 30-50 символов (макс 100)
  * Стиль: информативный, SEO-оптимизированный
  * Ключевые слова в начале (первые 40 символов видны в интерфейсе)
  * От первого лица, без кликбейта
  * Обязательно добавь #Shorts в конце
  * Пример: "Как я победил босса за 30 секунд | Лайфхак #Shorts"

- **Описание** (youtube_description):
  * Расширенная информация с ключевыми словами
  * 1-3 релевантных хештега
  * Конкретные факты и результаты
  * Пример: "Показываю секретную тактику которая помогла мне победить сложнейшего босса всего за 30 секунд. Работает в 90% случаев!\n\n#gaming #геймплей #лайфхак"

🎵 TIKTOK (⚠️ У TikTok ДВА отдельных поля!):

- **Title** (tiktok_title):
  * Длина: 20-40 символов
  * SEO и поиск: короткий заголовок с ключевыми словами
  * Что именно показано в видео
  * БЕЗ хештегов (хештеги только в description)
  * Пример: "Как победить босса за 30 секунд"

- **Description/Caption** (tiktok_description):
  * Длина: 50-150 символов (оптимально)
  * Хук в первых словах для привлечения внимания
  * ОБЯЗАТЕЛЬНО включи CTA (Call-to-Action): "Сохрани!", "А ты так делаешь?", "Напиши в комментах"
  * 3-5 релевантных хештегов в конце
  * Трендовые + нишевые хештеги
  * От первого лица, прямой и вовлекающий тон
  * Пример: "Этот трюк сэкономил мне 2 часа попыток 😱 Сохрани чтобы не потерять! А ты знал этот секрет? Напиши в комментах 👇 #gaming #геймплей #лайфхак #тикток #босс"

📸 INSTAGRAM REELS:
- **Caption** (instagram_description):
  * Длина: до 150 символов (первые 125 видны до "...ещё")
  * Эмоциональный хук в первых 125 символах
  * 3-5 эмодзи для визуального акцента
  * От первого лица, личная история
  * Призыв: "Поделись с другом", "Сохрани на потом"
  * 3-5 хештегов в конце
  * Эстетичное форматирование с абзацами
  * Пример: "Я не верил что это сработает 😱 Но этот трюк изменил всё! 🎮 Теперь я прохожу боссов в 10 раз быстрее ✨\n\nПопробуй сам и напиши что получилось 👇 Кто со мной?\n\n#gaming #геймплей #лайфхак #gamer #мотивация"

🔑 ОБЩИЕ ПРАВИЛА ДЛЯ ВСЕХ ПЛАТФОРМ:
- Пиши от первого лица (я, мне, мой опыт)
- Используй конкретные цифры и факты (30 секунд, 2 часа, 90%, 10 раз)
- Эмоциональные триггеры: удивление, любопытство, мотивация
- Хештеги ТОЛЬКО релевантные содержанию
- НЕ выдумывай названия игр — используй только распознаваемые из транскрипта
- Если игра неясна — используй нейтральные теги (#gaming #геймплей #gamer)

ПЕРЕДАЧА И ОБОГАЩЕНИЕ CLIENT_META:
- Если входные данные включают {{ $json.client_meta }}, сохрани ВСЕ существующие поля внутри него.
- Добавь следующие НОВЫЕ поля в client_meta для каждого клипа:
  * "youtube_title" — заголовок для YouTube Shorts (30-50 символов, SEO, #Shorts в конце)
  * "youtube_description" — описание для YouTube (информативное, ключевые слова, 1-3 хештега)
  * "tiktok_title" — заголовок для TikTok (20-40 символов, SEO, БЕЗ хештегов)
  * "tiktok_description" — description/caption для TikTok (50-150 символов, хук + CTA + 3-5 хештегов)
  * "instagram_description" — caption для Instagram (до 150 символов, эмоциональный хук + эмодзи + 3-5 хештегов)
  * "virality_score" — число с плавающей точкой (7.5–10.0)
  * "virality_reason" — краткое объяснение по-русски (1-3 предложения)
- НЕ удаляй и не перезаписывай поля, которые уже были в client_meta на входе.
- Верни обогащённый объект client_meta в JSON-выводе каждого клипа.

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

CLIENT_META (входные данные, могут быть пустыми или содержать существующие поля):
{{ JSON.stringify($json.client_meta || {}) }}

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
- ⚠️ КРИТИЧНО: **ПЕРВЫЙ субтитр ОБЯЗАТЕЛЬНО должен начинаться с 0.0** (start: 0.0), а не с задержкой!
  * Сдвигай start первого субтитра на 0.0, НО end оставляй без изменений
  * Это гарантирует что текст появится сразу, без пустого экрана в начале
  * Пример: если первый субтитр был {"text": "Привет", "start": 0.2, "end": 1.5}, измени на {"text": "Привет", "start": 0.0, "end": 1.5}

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
      "client_meta": {
        ...существующие поля из входного client_meta (если есть)...,
        "youtube_title": "<30-50 символов, SEO, от первого лица, ключевые слова в начале, #Shorts в конце>",
        "youtube_description": "<информативное описание с ключевыми словами, конкретные факты, 1-3 хештега>",
        "tiktok_title": "<20-40 символов, SEO-заголовок с ключевыми словами, БЕЗ хештегов>",
        "tiktok_description": "<50-150 символов, хук в начале + CTA ('Сохрани!', 'Напиши в комментах') + 3-5 хештегов>",
        "instagram_description": "<до 150 символов, эмоциональный хук + 3-5 эмодзи + призыв ('Сохрани', 'Поделись') + 3-5 хештегов>",
			  "duration": <<end>-<start> ISO 8601 duration format, e.g. PT1M39S>,
        "duration_ms": <number miliseconds <end>-<start>, e.g. 99000>,
        "virality_score": <float, например 9.5>,
        "virality_reason": "<1-3 предложения по-русски, почему этот момент вирусный>"
      }
    }
  ]
}

ПРИМЕР КОНВЕРТАЦИИ СУБТИТРОВ:
Если clip.start = 100.0 и слова в МАССИВ_СЛОВ это:
- {"w": "привет", "s": 100.5, "e": 101.2}
- {"w": "всем", "s": 101.3, "e": 101.8}
- {"w": "сегодня", "s": 102.0, "e": 102.7}

Тогда в массиве subtitles:
- {"text": "привет", "start": 0.0, "end": 1.2}  ← ПЕРВЫЙ субтитр: start сдвинут на 0.0!
- {"text": "всем", "start": 1.3, "end": 1.8}
- {"text": "сегодня", "start": 2.0, "end": 2.7}

ПРИМЕР ОБОГАЩЕНИЯ CLIENT_META:
Входные данные client_meta: {"user_id": "abc123", "campaign": "winter2025"}
Выходные данные client_meta для клипа: {"user_id": "abc123", "campaign": "winter2025", "caption": "...", "video_description_for_tiktok": "...", "video_description_for_instagram": "...", "video_title_for_youtube_short": "...", "duration":"PT1M39S", "duration_ms":"99000", "virality_score": 9.2, "virality_reason": "..."}

⚠️ КРИТИЧНО: 
- Таймкоды субтитров ДОЛЖНЫ быть относительными от начала клипа (вычитай clip.start из всех таймкодов слов).
- Сохраняй ВСЕ входящие поля client_meta и добавляй новые; НЕ заменяй весь объект.
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
  fontsize: 72,  // Увеличен для лучшей видимости в превью
  fontcolor: "black",  // Чёрный текст
  bordercolor: "white",  // Белая обводка (создаёт эффект белого фона)
  borderw: 8,  // Толстая обводка для эффекта фона
  box: 1,  // Включаем box для белого фона
  boxcolor: "white@0.85",  // Полупрозрачный белый фон
  boxborderw: 20,  // Отступы вокруг текста
  y: 250,  // Позиция заголовка (оптимизированная для композиции)
  start_time: 0.0,  // КРИТИЧНО: С ПЕРВОГО КАДРА для красивых превью на YouTube/TikTok
  duration: 5,  // Увеличена длительность показа
  fade_in: 0.3,  // Быстрое появление
  fade_out: 0.5
};

const subtitle_config = {
  fontsize: 68,  // Увеличен для лучшей читаемости на TikTok/Shorts
  fontcolor: "black",  // Чёрный текст для контраста с белым фоном
  bordercolor: "white",  // Белая обводка
  borderw: 6,  // Толстая обводка для жирности
  box: 1,  // Включаем box для белого фона
  boxcolor: "white@0.90",  // Белый полупрозрачный фон
  boxborderw: 15,  // Отступы вокруг текста
  y: "h-350"  // Позиция субтитров (оптимизированная для композиции)
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
  client_meta: {
    ...(short.client_meta || {}),
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

## Настройки для идеальных превью на YouTube/TikTok

### Ключевые параметры для красивых превью:

**1. Заголовок должен быть виден с первого кадра:**
```javascript
start_time: 0.0  // КРИТИЧНО! YouTube/TikTok берут превью с 0-1 секунды
duration: 5      // Достаточно долго чтобы зритель прочитал
```

**2. Белый фон для заголовка (лучшая читаемость):**
```javascript
fontcolor: "black",           // Чёрный текст хорошо читается
box: 1,                       // Включаем фоновый box
boxcolor: "white@0.85",      // Полупрозрачный белый фон
boxborderw: 20,              // Отступы вокруг текста
bordercolor: "white",        // Белая обводка
borderw: 8                   // Толстая обводка для "жирности"
```

**3. Крупный и жирный шрифт:**
```javascript
fontsize: 72  // Заметно больше для привлечения внимания
```

**4. Позиционирование:**
```javascript
y: 250        // Верхняя часть экрана - хорошо видно в превью
```

### Почему это важно:

- **YouTube Shorts**: Генерирует превью из первых 1-2 секунд видео
- **TikTok**: Автоматическая обложка берётся с начала видео
- **Instagram Reels**: Первый кадр = ваша обложка в ленте

**Без заголовка на первом кадре** = скучное превью = меньше кликов = меньше просмотров

### Рекомендуемая конфигурация title_config:

```javascript
const title_config = {
  fontsize: 72,                    // Крупно и заметно
  fontcolor: "black",              // Чёрный текст на белом фоне
  bordercolor: "white",            // Белая обводка
  borderw: 8,                      // Жирная обводка
  box: 1,                          // Белый фон включён
  boxcolor: "white@0.85",         // 85% непрозрачности
  boxborderw: 20,                 // Отступы для "воздуха"
  y: 250,                         // Верхняя часть экрана
  start_time: 0.0,                // С ПЕРВОГО КАДРА!
  duration: 5,                    // 5 секунд показа
  fade_in: 0.3,                   // Быстрое появление
  fade_out: 0.5                   // Плавное исчезновение
};
```

### Рекомендуемая конфигурация subtitle_config:

```javascript
const subtitle_config = {
  fontsize: 68,                    // Жирнее обычного
  fontcolor: "black",              // Чёрный на белом
  bordercolor: "white",            // Белая обводка
  borderw: 6,                      // Толстая обводка
  box: 1,                          // Белый фон
  boxcolor: "white@0.90",         // Высокая непрозрачность
  boxborderw: 15,                 // Отступы
  y: "h-350"                      // Нижняя часть экрана
};
```

## Troubleshooting

**Субтитры не синхронны** → LLM должен вычесть `clip.start` из всех таймкодов
**Слишком много текста** → Уменьшите слова в фразе (2-4 слова) или `fontsize`
**Текст обрезается** → API автоматически переносит, но лучше короче фразы (2-4 слова)
**Плохая контрастность** → Увеличьте `borderw` до 6-8 и используйте `box` с белым фоном
**Превью на YouTube/TikTok пустое** → Убедитесь что `title_config.start_time: 0.0` (не 0.5!)
**Текст плохо читается** → Используйте чёрный текст (`fontcolor: "black"`) на белом фоне (`box: 1, boxcolor: "white@0.85"`)
