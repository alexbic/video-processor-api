# Шрифты в Video Processor API

## Доступные шрифты

**10 оптимизированных шрифтов**, гарантированно работающих с FFmpeg.

### Финальный набор (10 шрифтов):
1. **HelveticaNeue** - премиум Sans-Serif
2. **LucidaGrande** - элегантный Sans-Serif
3. **COPPERPLATE** - декоративный стиль
4. **Charter** - современный Serif
5. **PTSans** - русский шрифт
6. **Monaco** - Monospace
7. **MarkerFelt** - креативный стиль
8. **Palatino** - классический Serif
9. **STIXTwoText-Italic** - научный шрифт
10. **Menlo** - Monospace

---

## Использование в API

### Получить список доступных шрифтов

```bash
curl http://localhost:5001/fonts
```

### Пример запроса с одним из доступных шрифтов

```bash
curl -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "operations": [{
      "type": "make_short",
      "text_items": [{
        "text": "Мой Shorts",
        "fontfile": "HelveticaNeue.ttc",
        "fontsize": 70,
        "fontcolor": "white",
        "y": 250,
        "x": "(w-text_w)/2"
      }]
    }]
  }'
```

---

## Рекомендации по выбору

### Для социальных сетей (TikTok/Instagram Reels/YouTube Shorts):
- **Заголовки:** HelveticaNeue, LucidaGrande
- **Текст на экране:** PTSans, Charter
- **Креатив:** MarkerFelt

### Для профессионального контента:
- **Основной текст:** Charter, Palatino
- **Заголовки:** HelveticaNeue, LucidaGrande
- **Технический контент:** Menlo, Monaco

### Для образовательного контента:
- **Математика:** STIXTwoText-Italic
- **Общий текст:** PTSans, Charter
- **Выделение:** COPPERPLATE

---

## Миграция с более старых версий

Если вы используете шрифты, которых нет в v1.0.0:

- **Avenir** → используйте **HelveticaNeue**
- **Didot** → используйте **Charter** или **Palatino**
- **Futura** → используйте **PTSans** или **Charter**
- Другие → используйте **HelveticaNeue** (универсальный выбор)

---

## Встроенные системные шрифты (Legacy)

При сборке Docker контейнера устанавливаются следующие популярные шрифты:

### Sans-Serif (без засечек)
- **DejaVu Sans** - универсальный шрифт, хорошая поддержка Unicode
  - `font: 'DejaVu Sans'`
  - `fontfile: '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'`

- **DejaVu Sans Bold** - жирное начертание
  - `font: 'DejaVu Sans Bold'`
  - `fontfile: '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'`

- **Liberation Sans** - альтернатива Arial
  - `font: 'Liberation Sans'`
  - `fontfile: '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'`

- **Noto Sans** - современный Google шрифт
  - `font: 'Noto Sans'`
  - `fontfile: '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'`

- **Roboto** - популярный шрифт Android
  - `font: 'Roboto'`
  - `fontfile: '/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf'`

- **Open Sans** - веб-шрифт, очень читабельный
  - `font: 'Open Sans'`
  - `fontfile: '/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf'`

### Serif (с засечками)
- **DejaVu Serif**
  - `font: 'DejaVu Serif'`
  - `fontfile: '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'`

- **Liberation Serif** - альтернатива Times New Roman
  - `font: 'Liberation Serif'`
  - `fontfile: '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'`

### Monospace (моноширинные)
- **Liberation Mono** - для кода и техно-стиля
  - `font: 'Liberation Mono'`
  - `fontfile: '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf'`

---

## Кастомные шрифты пользователя

### Как добавить свои шрифты:

1. **Создайте директорию для шрифтов на хосте:**
   ```bash
   mkdir -p /opt/n8n-docker/volumes/video_processor/fonts
   ```

2. **Скопируйте ваши .ttf или .otf файлы:**
   ```bash
   cp /path/to/YourFont.ttf /opt/n8n-docker/volumes/video_processor/fonts/
   ```

3. **Перезапустите контейнер (если нужно):**
   ```bash
   docker restart video-processor
   ```

4. **Проверьте доступные шрифты через API:**
   ```bash
   curl http://localhost:5001/fonts
   ```

### Использование кастомного шрифта в запросе:

**Через fontfile (рекомендуется):**
```json
{
  "operations": [{
    "type": "make_short",
    "text_items": [{
      "text": "Заголовок",
      "fontfile": "YourFont.ttf",
      "fontsize": 60,
      "x": "(w-text_w)/2",
      "y": 100
    }]
  }]
}
```

**Полный путь (альтернатива):**
```json
{
  "text_items": [{
    "text": "Заголовок",
    "fontfile": "/app/fonts/custom/YourFont.ttf",
    "fontsize": 60
  }]
}
```

---

## API Endpoint: GET /fonts

Возвращает список всех доступных шрифтов (системных + кастомных).

**Пример запроса:**
```bash
curl http://video-processor:5001/fonts
```

**Пример ответа:**
```json
{
  "status": "success",
  "total_fonts": 10,
  "fonts": [
    {
      "name": "HelveticaNeue",
      "family": "sans-serif",
      "file": "/app/fonts/HelveticaNeue.ttc"
    },
    {
      "name": "Charter",
      "family": "serif",
      "file": "/app/fonts/Charter.ttc"
    }
  ]
}
```

---

## Примеры использования

### Пример 1: Заголовок с HelveticaNeue
```json
{
  "video_url": "https://example.com/video.mp4",
  "operations": [{
    "type": "make_short",
    "text_items": [{
      "text": "Мой Shorts",
      "fontfile": "HelveticaNeue.ttc",
      "fontsize": 70,
      "fontcolor": "yellow",
      "x": "(w-text_w)/2",
      "y": 100
    }]
  }]
}
```

### Пример 2: Русский текст с PTSans
```json
{
  "text_items": [{
    "text": "Привет мир!",
    "fontfile": "PTSans.ttc",
    "fontsize": 64,
    "fontcolor": "white",
    "x": "(w-text_w)/2",
    "y": "h-200",
    "start": 0,
    "end": 5
  }]
}
```

### Пример 3: Кастомный шрифт с фоновой плашкой
```json
{
  "text_items": [{
    "text": "Стильный заголовок",
    "fontfile": "/app/fonts/custom/CustomFont-Bold.ttf",
    "fontsize": 80,
    "fontcolor": "#FF00FF",
    "x": "(w-text_w)/2",
    "y": 150,
    "box": 1,
    "boxcolor": "black@0.6",
    "boxborderw": 15
  }]
}
```

### Пример 4: Два текстовых элемента с разными шрифтами
```json
{
  "text_items": [
    {
      "text": "Заголовок",
      "fontfile": "HelveticaNeue.ttc",
      "fontsize": 70,
      "fontcolor": "white",
      "x": "(w-text_w)/2",
      "y": 100,
      "start": 0,
      "end": 60
    },
    {
      "text": "Подписывайся!",
      "fontfile": "Charter.ttc",
      "fontsize": 48,
      "fontcolor": "yellow",
      "x": "(w-text_w)/2",
      "y": "h-200",
      "start": 0,
      "end": 3
    }
  ]
}
```

**Note:** Public version supports max **2 text items** per operation.

---

## Технические детали

- **Формат:** Смесь `.ttc` и `.ttf` файлов
- **Кодировка:** UTF-8 (полная поддержка кириллицы)
- **FFmpeg совместимость:** 100% (все 10 протестированы)
- **Размер папки fonts:** ~8.8 MB
- **Производительность:** Оптимизировано для быстрого рендеринга
- **Тестирование:** Все шрифты протестированы с FFmpeg на специальном полигоне

---

## Troubleshooting

**Шрифт не найден:**
```
Error: Font not found
```
**Решение:** Проверьте список доступных шрифтов через `GET /fonts`.

**Кастомный шрифт не отображается:**
1. Проверьте что файл .ttf/.otf лежит в `/opt/n8n-docker/volumes/video_processor/fonts/`
2. Проверьте права доступа: `chmod 644 /opt/.../fonts/*.ttf`
3. Перезапустите контейнер: `docker restart video-processor`

**Текст отображается квадратиками:**
- Используйте PTSans для русского текста
- Используйте DejaVu Sans или Noto Sans (лучшая поддержка Unicode)
- Убедитесь что шрифт поддерживает нужные символы (кириллицу, эмодзи и т.д.)

---

## История версий

| Версия | Шрифтов | Статус | Примечание |
|--------|---------|--------|-----------|
| v1.2.0 | 41 | Legacy | Архив: старая версия |
| v1.0.0 | 10 | **Текущая** | Финальный оптимизированный релиз |
