# 🎨 Video Templates System

## Обзор

Система из **60 уникальных видеошаблонов** для оформления клипов с красивыми неоновыми обводками текста.

## 📁 Файлы

- **`templates-definitions.js`** - 60 шаблонов с полным описанием стилей
- **`apply-templates.js`** - N8N код node для применения шаблонов к клипам

## 🎯 4 Категории Шаблонов

### 1. ✨ NEON_GLOW (15 шт)
- Заголовок на плашке БЕЗ обводки
- Субтитры БЕЗ плашки, НО С толстой цветной обводкой
- Примеры: Cyber Neon, Fire & Ice, Gold & Purple, Toxic Green

### 2. 📦 SOLID_FRAMES (15 шт)
- Оба текста (title + subtitles) на плашках
- Минимальные обводки
- Примеры: Double Neon, Double Impact, Double Gold

### 3. ⚡ OUTLINE_PURE (15 шт)
- БЕЗ плашек - только текст с ТОЛСТЫМИ контрастными обводками
- Максимальная читаемость
- Примеры: Outline Neon, Outline Classic, Outline Blood

### 4. 🔀 CREATIVE_MIX (15 шт)
- Смешанные вариации (плашка + обводка, разные комбинации)
- Примеры: Hybrid Neon Mix, Hybrid Fire Outline, Hybrid Ocean Wave

## ✨ Особенности Обводок (STROKE)

Каждый шаблон содержит:
- **`borderw`** - толщина обводки (0-17 пиксел)
- **`bordercolor`** - цвет обводки в hex формате

### Как это работает

```javascript
// Пример из шаблона "Cyber Neon"
sub: {
  fontfile: "PTSans.ttc",
  fontsize: 75,
  fontcolor: "#FF00FF",          // Bright fuchsia текст
  bordercolor: "#000000",        // Чёрная обводка
  borderw: 14,                   // Толщина 14px
  // ...
}
```

## 🎲 Случайный Выбор Шаблона

Файл `apply-templates.js` автоматически:
1. Получает входящий клип с субтитрами
2. Выбирает случайный шаблон из 60 доступных
3. Применяет стили title и subtitles
4. Передаёт в backend для генерации видео

### Фильтрация по категории

```javascript
// Если в client_meta передать:
{
  "template_category": "NEON_GLOW"
}
// Тогда выбор будет только из 15 шаблонов NEON_GLOW
```

### Фильтрация по жанру

```javascript
// Если в client_meta передать:
{
  "template_genre": "gaming"
}
// Тогда выбор будет из шаблонов, помеченных как best_for: "gaming"
```

## 🖼️ Список Всех Шаблонов

### NEON_GLOW
1. cyber_neon
2. fire_ice
3. gold_purple
4. toxic_green
5. electric_yellow
6. blood_shadow
7. matrix_code
8. royal_blue
9. lava_glow
10. cosmic_purple
11. neon_pink
12. sunset_orange
13. arctic_blue
14. crimson_rage
15. emerald_shine

### SOLID_FRAMES
16. double_neon
17. double_impact
18. double_elegant
19. double_toxic
20. double_gold
21. double_cyber
22. double_fire
23. double_ice
24. double_purple
25. double_clean
26. double_sunset
27. double_ocean
28. double_forest
29. double_volcano
30. double_midnight

### OUTLINE_PURE
31. outline_neon
32. outline_fire
33. outline_classic
34. outline_rainbow
35. outline_gold
36. outline_toxic
37. outline_blood
38. outline_ice
39. outline_purple
40. outline_contrast
41. outline_electric
42. outline_sunset
43. outline_emerald
44. outline_ruby
45. outline_sapphire

### CREATIVE_MIX
46. hybrid_neon_mix
47. hybrid_fire_outline
48. hybrid_gold_shadow
49. hybrid_ice_fire
50. hybrid_purple_glow
51. hybrid_toxic_warning
52. hybrid_ocean_wave
53. hybrid_sunset_dream
54. hybrid_forest_light
55. hybrid_blood_moon
56. hybrid_crystal_clear
57. hybrid_lava_stone
58. hybrid_electric_storm
59. hybrid_shadow_light
60. hybrid_neon_city

## 🎨 Доступные Шрифты

1. **Charter.ttc** - Modern Serif
2. **Copperplate.ttc** - Декоративный стиль
3. **HelveticaNeue.ttc** - Premium Sans-Serif
4. **LucidaGrande.ttc** - Элегантный Sans-Serif
5. **MarkerFelt.ttc** - Креативный стиль
6. **Menlo.ttc** - Monospace
7. **Monaco.ttf** - Monospace
8. **PTSans.ttc** - Русский шрифт
9. **Palatino.ttc** - Классический Serif
10. **STIXTwoText-Italic.ttf** - Научный

## 🔧 Backend Integration

Backend (`app.py`) теперь поддерживает параметры обводки:
- **`borderw`** - ширина обводки (проходит в FFmpeg drawtext)
- **`bordercolor`** - цвет обводки (проходит в FFmpeg drawtext)

Это означает что все обводки из шаблонов **будут видны** в генерируемых видео!

## 📋 Формат Input для apply-templates.js

```json
{
  "json": {
    "start": 125.5,
    "end": 205.8,
    "title": "Эпичная битва",
    "subtitles": [
      {
        "text": "Вот это момент",
        "start": 0.0,
        "end": 2.5
      }
    ],
    "source_video_url": "http://...",
    "client_meta": {
      "template_category": "NEON_GLOW",
      "user_id": "abc123"
    }
  }
}
```

## 📤 Формат Output от apply-templates.js

```json
{
  "json": {
    "video_url": "http://...",
    "execution": "async",
    "operations": [{
      "type": "make_short",
      "start_time": 125.5,
      "end_time": 205.8,
      "crop_mode": "letterbox",
      "text_items": [
        {
          "text": "Эпичная битва",
          "fontfile": "HelveticaNeue.ttc",
          "fontcolor": "#FF00FF",
          "borderw": 14,
          "bordercolor": "#000000",
          "start": 0.0,
          "end": 7.0
        },
        {
          "text": "",
          "fontfile": "PTSans.ttc",
          "fontcolor": "#FF00FF",
          "borderw": 14,
          "bordercolor": "#000000",
          "subtitles": {
            "items": [...]
          }
        }
      ]
    }],
    "client_meta": {
      "_template_key": "cyber_neon",
      "_template_name": "Cyber Neon",
      "_template_category": "NEON_GLOW",
      "_templates_available": 15
    }
  }
}
```

## ✅ Что Происходит Сейчас

1. **Клип поступает** с субтитрами и метаданными
2. **apply-templates.js** выбирает случайный шаблон
3. **Применяются стили** (шрифт, цвет, обводка)
4. **Передаётся в backend** с параметрами borderw и bordercolor
5. **FFmpeg генерирует видео** с красивыми обводками текста

## 🎬 Результат

✅ Видео с красивыми неоновыми обводками вокруг текста  
✅ Каждый клип получает уникальный случайный дизайн  
✅ Обводки правильно контрастируют с цветом текста  
✅ Поддерживаются все 60 шаблонов  

## 🐛 Решённые Проблемы

- ✅ **Проблема:** Обводки были описаны в шаблонах но не генерировались
- ✅ **Причина:** Backend не обрабатывал параметры borderw и bordercolor
- ✅ **Решение:** Добавлены параметры обводки в app.py drawtext фильтр
- ✅ **Результат:** Теперь обводки видны в видео!
