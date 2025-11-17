# 🎮 Gaming Template Selector - Руководство по использованию

## 📋 Обзор

Gaming Template Selector v3.0 - улучшенный селектор шаблонов с **фильтрацией по тематике**.

**Возможности:**
- ✅ 30 gaming шаблонов с кириллицей
- ✅ Фильтрация по категории (GAMING_CONTRAST, DOUBLE_BOX, NO_BOX)
- ✅ Фильтрация по жанру игры (cyberpunk, rpg, horror, racing, etc.)
- ✅ Выбор конкретного шаблона по имени
- ✅ Случайный выбор из всех шаблонов (по умолчанию)

---

## 🎯 Как использовать фильтрацию

### 1. Случайный выбор из всех 30 шаблонов (по умолчанию)

**Не передавай никаких параметров** - выберется случайный шаблон:

```json
{
  "shorts": {
    "title": "Невероятный момент!",
    "start": 10.5,
    "end": 70.2,
    "subtitles": [...],
    "client_meta": {}
  }
}
```

---

### 2. Фильтрация по категории

Добавь `template_category` в `client_meta`:

```json
{
  "shorts": {
    "title": "Эпичный момент!",
    "start": 10.5,
    "end": 70.2,
    "subtitles": [...],
    "client_meta": {
      "template_category": "GAMING_CONTRAST"
    }
  }
}
```

**Доступные категории:**
- `"GAMING_CONTRAST"` (10 шаблонов) - заголовок на плашке, субтитры без
- `"DOUBLE_BOX"` (10 шаблонов) - оба на плашках
- `"NO_BOX"` (10 шаблонов) - только обводка, мем-стиль

---

### 3. Фильтрация по жанру

Добавь `template_genre` в `client_meta`:

```json
{
  "shorts": {
    "title": "Кибер-атака началась",
    "start": 10.5,
    "end": 70.2,
    "subtitles": [...],
    "client_meta": {
      "template_genre": "cyberpunk"
    }
  }
}
```

**Доступные жанры:**
- `"cyberpunk"` - киберпанк, tech, sci-fi
- `"action"` - экшен, battle, pvp
- `"rpg"` - ролевые игры, fantasy, magic
- `"horror"` - хорроры, zombie, survival, dark
- `"racing"` - гонки, speed, energy
- `"strategy"` - стратегии, empire, rts
- `"boss"` - босс-файты, epic
- `"space"` - космос, cosmic, alien
- `"important"` - важная информация, tutorial
- `"poison"` - яды, radioactive, acid
- `"frost"` - мороз, winter, frozen
- `"magic"` - магия, arcane, fantasy
- `"meme"` - мемы, viral, classic
- `"fun"` - весёлое, colorful, happy

---

### 4. Комбинация фильтров (категория + жанр)

Можно комбинировать фильтры для точного выбора:

```json
{
  "shorts": {
    "title": "Рейд на босса!",
    "start": 10.5,
    "end": 70.2,
    "subtitles": [...],
    "client_meta": {
      "template_category": "GAMING_CONTRAST",
      "template_genre": "rpg"
    }
  }
}
```

**Как это работает:**
1. Сначала фильтруется по категории (GAMING_CONTRAST → 10 шаблонов)
2. Затем фильтруется по жанру (rpg → 1 шаблон: "Gold & Purple")
3. Если подходящих шаблонов несколько - выбирается случайный

---

### 5. Конкретный шаблон по имени

Если нужен **точный шаблон**, используй `template_name`:

```json
{
  "shorts": {
    "title": "Матрица активирована",
    "start": 10.5,
    "end": 70.2,
    "subtitles": [...],
    "client_meta": {
      "template_name": "matrix_code"
    }
  }
}
```

**Доступные имена шаблонов:**

#### GAMING_CONTRAST (10):
- `"cyber_neon"` - Cyber Neon
- `"fire_ice"` - Fire & Ice
- `"gold_purple"` - Gold & Purple
- `"toxic_green"` - Toxic Green
- `"electric_yellow"` - Electric Yellow
- `"blood_shadow"` - Blood Shadow
- `"matrix_code"` - Matrix Code
- `"royal_blue"` - Royal Blue
- `"lava_glow"` - Lava Glow
- `"cosmic_purple"` - Cosmic Purple

#### DOUBLE_BOX (10):
- `"double_neon"` - Double Neon
- `"double_impact"` - Double Impact
- `"double_elegant"` - Double Elegant
- `"double_toxic"` - Double Toxic
- `"double_gold"` - Double Gold
- `"double_cyber"` - Double Cyber
- `"double_fire"` - Double Fire
- `"double_ice"` - Double Ice
- `"double_purple"` - Double Purple
- `"double_clean"` - Double Clean

#### NO_BOX (10):
- `"outline_neon"` - Outline Neon
- `"outline_fire"` - Outline Fire
- `"outline_classic"` - Outline Classic (классический мем-стиль)
- `"outline_rainbow"` - Outline Rainbow
- `"outline_gold"` - Outline Gold
- `"outline_toxic"` - Outline Toxic
- `"outline_blood"` - Outline Blood
- `"outline_ice"` - Outline Ice
- `"outline_purple"` - Outline Purple
- `"outline_contrast"` - Outline Contrast

---

## 📊 Метаданные в ответе

После обработки в `client_meta` добавляются данные о выбранном шаблоне:

```json
{
  "client_meta": {
    "_template_key": "cyber_neon",
    "_template_name": "Cyber Neon",
    "_template_category": "GAMING_CONTRAST",
    "_template_genres": ["cyberpunk", "tech", "sci-fi"],
    "_templates_available": 3
  }
}
```

**Параметры:**
- `_template_key` - ключ шаблона (для повторного использования)
- `_template_name` - красивое название
- `_template_category` - категория шаблона
- `_template_genres` - список подходящих жанров
- `_templates_available` - сколько шаблонов подошло под фильтры

---

## 🎨 Примеры для разных жанров

### Cyberpunk / Tech
```json
{
  "client_meta": {
    "template_genre": "cyberpunk"
  }
}
```
**Варианты:** Cyber Neon, Matrix Code, Double Cyber, Outline Neon

---

### RPG / Fantasy
```json
{
  "client_meta": {
    "template_genre": "rpg"
  }
}
```
**Варианты:** Gold & Purple, Double Purple, Outline Purple

---

### Horror / Dark
```json
{
  "client_meta": {
    "template_genre": "horror"
  }
}
```
**Варианты:** Toxic Green, Blood Shadow, Double Toxic, Outline Blood

---

### Action / Battle
```json
{
  "client_meta": {
    "template_genre": "action"
  }
}
```
**Варианты:** Fire & Ice, Double Fire, Outline Fire

---

### Racing / Speed
```json
{
  "client_meta": {
    "template_genre": "racing"
  }
}
```
**Варианты:** Electric Yellow, Outline Fire

---

### Bosses / Epic Moments
```json
{
  "client_meta": {
    "template_genre": "boss"
  }
}
```
**Варианты:** Lava Glow, Double Gold, Outline Gold

---

## 💡 Best Practices

### 1. Для вирусного контента
Используй **NO_BOX** категорию - классический мем-стиль:
```json
{
  "client_meta": {
    "template_category": "NO_BOX"
  }
}
```

### 2. Для важных гайдов/туториалов
Используй **DOUBLE_BOX** - максимальная читаемость:
```json
{
  "client_meta": {
    "template_category": "DOUBLE_BOX",
    "template_genre": "important"
  }
}
```

### 3. Для динамичного контента
Используй **GAMING_CONTRAST** - акцент на заголовок:
```json
{
  "client_meta": {
    "template_category": "GAMING_CONTRAST"
  }
}
```

### 4. Для автоматического выбора по жанру
Передавай только жанр - селектор сам выберет лучший шаблон:
```json
{
  "client_meta": {
    "template_genre": "rpg"
  }
}
```

---

## 🔍 Отладка

### Посмотреть сколько шаблонов подошло
Проверь `_templates_available` в ответе:

```json
{
  "_templates_available": 1  // Нашёлся 1 шаблон
}
```

### Если подошло слишком мало шаблонов
- Уберите фильтр по жанру
- Используйте только category фильтр
- Проверьте правильность написания жанра

### Если нужна максимальная вариативность
Не передавайте фильтры - будут использованы все 30 шаблонов

---

## 📝 Интеграция с LLM

Если используешь LLM для генерации shorts, передавай жанр игры в промпте:

**Пример промпта для LLM:**
```
Проанализируй видео и создай shorts.
Игра: Cyberpunk 2077
Жанр: cyberpunk, action

Добавь в client_meta:
{
  "template_genre": "cyberpunk"
}
```

LLM добавит нужный жанр, и селектор автоматически выберет подходящий стиль.

---

## 🚀 Workflow файл

Используй файл: `/n8n-examples/n8n-30-gaming-templates-selector.json`

Импортируй в n8n → Настрой API key → Готово!

---

**Версия:** 3.0
**Дата обновления:** 2025-11-16
**Шаблонов:** 30
**Категорий:** 3
**Жанров:** 20+
