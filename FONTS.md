# Шрифты в Video Processor API

## Встроенные системные шрифты

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

**Вариант 1: Через font (имя файла без расширения):**
```json
{
  "title": {
    "text": "Заголовок",
    "font": "YourFont",
    "fontsize": 60
  }
}
```

**Вариант 2: Через fontfile (полный путь):**
```json
{
  "title": {
    "text": "Заголовок",
    "fontfile": "/app/fonts/custom/YourFont.ttf",
    "fontsize": 60
  }
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
  "total_fonts": 15,
  "fonts": {
    "system_fonts": [
      {
        "name": "DejaVu Sans",
        "family": "sans-serif",
        "file": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
      },
      {
        "name": "Roboto",
        "family": "sans-serif",
        "file": "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf"
      }
    ],
    "custom_fonts": [
      {
        "name": "YourFont",
        "family": "custom",
        "file": "/app/fonts/custom/YourFont.ttf"
      }
    ]
  }
}
```

---

## Примеры использования

### Пример 1: Заголовок с DejaVu Sans Bold
```json
{
  "inputs": [{"url": "https://example.com/video.mp4", "id": "main"}],
  "title": {
    "text": "Мой Shorts",
    "font": "DejaVu Sans Bold",
    "fontsize": 70,
    "fontcolor": "yellow"
  }
}
```

### Пример 2: Субтитры с Roboto
```json
{
  "subtitles": {
    "items": [
      {"text": "Первый субтитр", "start": 0, "end": 3}
    ],
    "font": "Roboto",
    "fontsize": 64,
    "fontcolor": "white"
  }
}
```

### Пример 3: Кастомный шрифт через fontfile
```json
{
  "title": {
    "text": "Стильный заголовок",
    "fontfile": "/app/fonts/custom/CustomFont-Bold.ttf",
    "fontsize": 80,
    "fontcolor": "#FF00FF"
  }
}
```

### Пример 4: Разные шрифты для title и subtitles
```json
{
  "title": {
    "text": "Заголовок",
    "font": "Open Sans Bold",
    "fontsize": 70
  },
  "subtitles": {
    "items": [{"text": "Субтитр", "start": 0, "end": 3}],
    "font": "Roboto",
    "fontsize": 64
  }
}
```

---

## Рекомендации по выбору шрифтов

### Для TikTok/Reels/Shorts:
- **Заголовки:** Open Sans Bold, Roboto Bold, Liberation Sans Bold
- **Субтитры:** DejaVu Sans, Roboto, Noto Sans

### Для профессионального контента:
- **Заголовки:** Liberation Sans, DejaVu Sans
- **Субтитры:** Roboto, Open Sans

### Для креативного контента:
- Используйте кастомные шрифты (загрузите свои .ttf файлы)

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
- Используйте DejaVu Sans или Noto Sans (лучшая поддержка Unicode)
- Убедитесь что шрифт поддерживает нужные символы (кириллицу, эмодзи и т.д.)
