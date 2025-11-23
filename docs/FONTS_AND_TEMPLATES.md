# Шрифты для текстовых оверлеев

## Проблема
Некоторые шрифты (Russo One, Oswald, Fixel) не полностью поддерживают кириллицу, что приводит к отображению "квадратиков" вместо букв при использовании русского текста.

## Решение
Все шаблоны обновлены для использования шрифтов с **100% поддержкой кириллицы** и полной совместимостью с FFmpeg drawtext фильтром.

## Рекомендуемые шрифты

### ✅ Основные (установлены в Dockerfile)
- **DejaVu Sans** - универсальный, все стили (Regular, Bold, etc.)
- **Montserrat** - чистый, современный вид
- **Liberation Sans** - свободная альтернатива Arial
- **Noto Sans** - поддержка множества языков

### Установленные пакеты
```dockerfile
fonts-dejavu-core
fonts-dejavu          # Полный набор
fonts-montserrat      # Все стили
fonts-liberation      # Полный набор
fonts-roboto          # Альтернатива
fonts-open-sans       # Альтернатива
fonts-noto-core       # Базовый набор
fonts-noto-cjk        # Поддержка CJK
fonts-noto-mono       # Моноширинный
```

## Использование в FFmpeg

Все шрифты вызываются **по названию**, а не по пути файла:

```bash
drawtext=fontfile='/path/to/font.ttf':text='текст'  # ❌ НЕ рекомендуется
drawtext=font='DejaVu Sans':text='текст'             # ✅ Рекомендуется
```

## Проверка поддержки шрифта

```bash
# Список всех шрифтов с поддержкой русского языка
fc-list :lang=ru

# Проверка конкретного шрифта
fc-list "DejaVu Sans"

# В контейнере
docker exec video-processor fc-list :lang=ru | grep "DejaVu Sans"
```

## Обновленные шаблоны

Файл `GAMING_TEMPLATES_FIXED.js` содержит 30 шаблонов с исправленными шрифтами:

- **GAMING_CONTRAST** (10): высокий контраст, яркие цвета
- **DOUBLE_BOX** (10): два текстовых блока в боксах
- **NO_BOX** (10): контурный текст без фона

### Примеры замен:

| Был | Теперь | Причина |
|-----|--------|---------|
| Russo One | DejaVu Sans | Cyrillic support ✅ |
| Oswald | DejaVu Sans | Cyrillic support ✅ |
| Fixel | Liberation Sans | Cyrillic support ✅ |
| Montserrat | Montserrat | ✅ Уже поддерживает |

## Тестирование

```bash
# Синхронный запрос с кириллицей
curl -X POST http://localhost:5001/process_video \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "...",
    "operations": [{
      "type": "make_short",
      "title": {
        "text": "Привет Мир!",
        "fontsize": 70
      },
      "subtitles": {
        "items": [
          {"text": "Первый субтитр", "start": 1, "end": 2}
        ]
      }
    }],
    "execution": "sync"
  }'
```

## Результаты

✅ ffprobe встроен в контейнер (для проверки видео)
✅ Все шрифты установлены и доступны
✅ Cyrillic rendering работает корректно (no squarish symbols)
✅ FFmpeg drawtext полностью совместим
✅ 30 шаблонов обновлены с правильными шрифтами

## Примечания

- При обновлении контейнера все шрифты кэшируются автоматически (`fc-cache -fv`)
- Шрифты ищутся по названию через fontconfig, поэтому сортировка регистронезависима
- Все изменения обратно совместимы с существующим API
