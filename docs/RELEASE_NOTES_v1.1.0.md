# 🎯 Video Processor API v1.1.0

Релиз с критическими исправлениями для production: валидация входных данных, полные URL в ответах, устранение редких 404 ошибок и фикс дублирования логов.

## 🆕 Новые возможности

### 🛡️ Валидация входных медиа-файлов
Предотвращает ошибки FFmpeg "moov atom not found" при попытке обработать HTML-страницы или некорректные файлы:

- **Проверка Content-Type**: отсекает `text/html`, `application/json` и другие не-медиа типы
- **Анализ сигнатур файлов**: распознаёт MP4 (`ftyp`), WebM/Matroska (EBML), MPEG-TS
- **Минимальный размер**: 100 KB порог для фильтрации страниц с ошибками
- **Атомарная запись**: использует временные `.part` файлы с последующим `os.replace()`
- **Понятные ошибки**: вместо cryptic FFmpeg errors возвращает:
  ```
  "URL returned HTML page, not media. Pass a direct media file URL."
  ```

**Пример ошибки раньше:**
```
error: "FFmpeg error: moov atom not found"
```

**Теперь:**
```json
{
  "status": "error",
  "error": "URL returned HTML page, not media. Pass a direct media file URL."
}
```

### 🔗 Полные абсолютные URL во всех ответах

**Исправлено:**
- `check_status_url` в async-ответах теперь полный URL вместо относительного пути
  - Было: `/task_status/{task_id}`
  - Стало: `http://video-processor:5001/task_status/{task_id}` или PUBLIC_BASE_URL

**Новая функция `build_absolute_url_background()`:**
- Для webhook payload и metadata.json в фоновых потоках
- Fallback на `INTERNAL_BASE_URL` (по умолчанию `http://video-processor:5001`)
- Гарантирует полные URL даже без request context

**Переменные окружения:**
```bash
PUBLIC_BASE_URL=https://example.com/video-processor-api  # Внешний URL (требует API_KEY)
INTERNAL_BASE_URL=http://video-processor:5001            # Внутренний Docker network URL
```

### 🔄 Filesystem Fallback для `/task_status`

Устраняет редкие 404 ошибки при проверке статуса завершённых задач:

**Новая логика:**
1. Поиск в Redis/memory (основное хранилище)
2. **Fallback:** чтение `tasks/{task_id}/metadata.json` если запись отсутствует
3. **Fallback:** статус "processing" если существует только директория задачи
4. Только затем 404

**Когда помогает:**
- Редкие случаи eviction ключей Redis (LRU)
- Перезапуск контейнера с memory storage
-Race conditions при старте воркеров
- Прямой доступ к metadata.json из внешних систем

### 📋 Сохранение порядка ключей в JSON (client_meta всегда внизу)

**Исправление для Flask 3.0:**
```python
app.json.sort_keys = False  # вместо устаревшего app.config['JSON_SORT_KEYS']
```

**Результат:**
```json
{
  "task_id": "abc-123",
  "status": "completed",
  "output_files": [...],
  "metadata_url": "...",
  "client_meta": {"source": "n8n"}  // ← всегда последний
}
```

Соответствует поведению `youtube-downloader-api` для унификации.

### 📊 Устранение дублирования startup-логов

При запуске с несколькими воркерами (`WORKERS=2+`) логи выводились N раз:

**Было (WORKERS=2):**
```
INFO:app:Video Processor API starting...
INFO:app:Storage mode: redis
INFO:app:Video Processor API starting...  // дубликат от 2-го воркера
INFO:app:Storage mode: redis              // дубликат
```

**Стало:**
```
INFO:app:Video Processor API starting...
INFO:app:Storage mode: redis
INFO:app:Workers (gunicorn): 2
```

**Реализация:**
- Атомарный маркер `/tmp/video_processor_api_start_logged`
- Первый воркер создаёт файл и выводит логи
- Остальные видят `FileExistsError` и пропускают

## 🐛 Исправления багов

### Критические
- **FFmpeg "moov atom not found"**: добавлена валидация перед обработкой
- **404 на /task_status**: filesystem fallback из metadata.json
- **Относительные URL в check_status_url**: теперь всегда полные
- **NameError в фоновом потоке**: исправлен отступ в `download_media_with_validation()`

### UI/UX
- **Дублирование логов**: один вывод на контейнер независимо от воркеров
- **Порядок ключей JSON**: `client_meta` всегда в конце ответа

## 🔧 Технические изменения

### Новые функции
```python
def download_media_with_validation(url: str, dest_path: str, timeout: int = 300) -> tuple[bool, str]
def build_absolute_url_background(path: str) -> str
def log_startup_info() -> None
def _log_startup_once() -> None
```

### Обновлённые endpoint responses

**POST /process_video (async):**
```json
{
  "task_id": "uuid",
  "status": "processing",
  "message": "Task created and processing in background",
  "check_status_url": "http://full-url/task_status/uuid",  // ← полный URL
  "client_meta": {...}  // ← последний ключ
}
```

**GET /task_status/{task_id}:**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "video_url": "...",
  "output_files": [
    {
      "filename": "output.mp4",
      "download_path": "/download/uuid/output/output.mp4",
      "download_url": "http://full-url/download/uuid/output/output.mp4"  // ← полный
    }
  ],
  "metadata_url": "http://full-url/download/uuid/metadata.json",
  "client_meta": {...}  // ← последний ключ
}
```

## 📦 Обновление

### Docker
```bash
docker pull alexbic/video-processor-api:v1.1.0
# или
docker pull alexbic/video-processor-api:latest
```

### Docker Compose
```yaml
services:
  video-processor:
    image: alexbic/video-processor-api:v1.1.0
    environment:
      - INTERNAL_BASE_URL=http://video-processor:5001  # новая переменная
      - PUBLIC_BASE_URL=https://example.com/api       # опционально
      - API_KEY=${API_KEY}                             # требуется с PUBLIC_BASE_URL
```

### Переменные окружения (новые/изменённые)
```bash
INTERNAL_BASE_URL=http://video-processor:5001  # Fallback URL для фоновых задач
WORKERS=2                                      # Теперь логи не дублируются
```

## ⚠️ Breaking Changes

**Нет breaking changes** — все изменения обратно совместимы.

Единственное: если вы парсили `check_status_url` как относительный путь, теперь он полный URL (но это исправление, не breaking change).

## 🧪 Тестирование

Все изменения протестированы локально:
- ✅ HTML URL → 400 с понятной ошибкой
- ✅ `check_status_url` → полный URL
- ✅ Fallback из metadata.json → completed статус
- ✅ JSON ключи → `client_meta` последний
- ✅ Startup логи → один раз при WORKERS=2

## 📝 Коммиты

- `87e2347` - feat: input validation, full URLs, filesystem fallback, JSON key order
- `2f840f3` - fix(logging): prevent duplicate startup logs with multiple workers

## 🤝 Благодарности

Спасибо за использование Video Processor API!

Если нашли баг или есть предложения — открывайте [Issue](https://github.com/alexbic/video-processor-api/issues).

---

**Предыдущая версия:** [v1.0.0](RELEASE_NOTES_v1.0.0.md)
