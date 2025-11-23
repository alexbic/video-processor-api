from flask import Flask, request, jsonify, send_file
import os
import subprocess
from datetime import datetime, timedelta
import uuid
import logging
import threading
from typing import Dict, Any
import socket
import re
import json
from functools import wraps
from bootstrap import wait_for_redis, log_tcp_port

app = Flask(__name__)
app.json.sort_keys = False
logger = logging.getLogger(__name__)

# ============================================
# API KEY AUTHENTICATION
# ============================================

PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL') or os.getenv('EXTERNAL_BASE_URL')
INTERNAL_BASE_URL = os.getenv('INTERNAL_BASE_URL')
API_KEY = os.getenv('API_KEY')  # Bearer token для авторизации

# Умная логика авторизации:
# - Если API_KEY не задан - работаем в режиме внутренней сети, PUBLIC_BASE_URL игнорируется
# - Если API_KEY задан - PUBLIC_BASE_URL активируется для генерации внешних ссылок
API_KEY_ENABLED = bool(API_KEY)  # Авторизация включена только если API_KEY задан

def require_api_key(f):
    """Декоратор для проверки API ключа через Bearer token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Если API_KEY не задан - пропускаем авторизацию
        if not API_KEY_ENABLED:
            return f(*args, **kwargs)
        
        # Проверяем Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header:
            return jsonify({
                'status': 'error',
                'error': 'Missing Authorization header',
                'message': 'Please provide API key via "Authorization: Bearer YOUR_API_KEY"'
            }), 401
        
        # Проверяем формат Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'status': 'error',
                'error': 'Invalid Authorization header format',
                'message': 'Expected format: "Authorization: Bearer YOUR_API_KEY"'
            }), 401
        
        token = parts[1]
        
        # Проверяем совпадение ключа
        if token != API_KEY:
            return jsonify({
                'status': 'error',
                'error': 'Invalid API key',
                'message': 'The provided API key is incorrect'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# URL HELPERS
# ============================================

def _join_url(base: str, path: str) -> str:
    if not base:
        return path
    return f"{base.rstrip('/')}/{path.lstrip('/')}"

def build_absolute_url(path: str) -> str:
    """Build absolute URL for a given API-relative path.

    Priority:
    1) PUBLIC_BASE_URL (only if API_KEY is set - public mode)
    2) Request host_url (when request context exists)
    3) Return path as-is (internal mode)
    """
    try:
        # PUBLIC_BASE_URL используется только если API_KEY задан (публичный режим)
        if API_KEY_ENABLED and PUBLIC_BASE_URL:
            return _join_url(PUBLIC_BASE_URL, path)
        # within request context
        if request and hasattr(request, 'host_url') and request.host_url:
            return _join_url(request.host_url, path)
    except Exception:
        pass
    return path

def build_absolute_url_background(path: str) -> str:
    """Build absolute URL in background context (no request available).

    Falls back to internal service URL if PUBLIC_BASE_URL not set.
    """
    if API_KEY_ENABLED and PUBLIC_BASE_URL:
        return _join_url(PUBLIC_BASE_URL, path)
    # Fallback: internal Docker network or localhost
    internal_base = INTERNAL_BASE_URL or 'http://video-processor:5001'
    return _join_url(internal_base, path)

def build_internal_url_background(path: str) -> str:
    """Build internal URL in background context (always uses INTERNAL_BASE_URL)."""
    internal_base = INTERNAL_BASE_URL or 'http://video-processor:5001'
    return _join_url(internal_base, path)

# ============================================
# TASK STORAGE - Redis (multi-worker) or In-Memory (single-worker)
# ============================================

# Public version: Built-in Redis (localhost), not configurable
# All Redis parameters are HARDCODED (no environment variables)
redis_client = None
REDIS_HOST = 'localhost'  # Built-in Redis (hardcoded)
REDIS_PORT = 6379         # Built-in Redis port (hardcoded)
REDIS_DB = 0              # Built-in Redis DB (hardcoded)
REDIS_INIT_RETRIES = 60   # More retries for built-in Redis startup (up to ~30s)
REDIS_INIT_DELAY_SECONDS = 0.5
STORAGE_MODE = "memory"

# Fallback: In-memory storage (only for single worker!)
tasks_memory: Dict[str, Dict[str, Any]] = {}

def _ensure_redis() -> bool:
    """Attempt to (re)initialize Redis client. Returns True on success."""
    global redis_client, STORAGE_MODE
    if redis_client is not None and STORAGE_MODE == "redis":
        return True
    try:
        import redis
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        client.ping()
        redis_client = client
        if STORAGE_MODE != "redis":
            logger.info(f"Redis connected at {REDIS_HOST}:{REDIS_PORT}")
        STORAGE_MODE = "redis"
        return True
    except Exception as e:
        # Покажем причину неудачного подключения всегда (для диагностики старта)
        logger.debug(f"Redis connect failed: {e}")
        if STORAGE_MODE != "memory":
            logger.warning(f"Redis unavailable, falling back to memory: {e}")
        STORAGE_MODE = "memory"
        redis_client = None
        return False

# Initialize at startup with retries to wait for Redis
import time
for _i in range(max(0, REDIS_INIT_RETRIES)):
    if _ensure_redis():
        break
    try:
        time.sleep(max(0.0, REDIS_INIT_DELAY_SECONDS))
    except Exception:
        pass

def save_task(task_id: str, task_data: dict):
    """Save task to Redis or memory"""
    # Lazy reconnection to Redis
    _ensure_redis()
    if STORAGE_MODE == "redis" and redis_client is not None:
        try:
            redis_ttl = TASK_TTL_HOURS * 3600  # Convert hours to seconds (72h = 259200s)
            redis_client.setex(
                f"task:{task_id}",
                redis_ttl,
                json.dumps(task_data)
            )
            return
        except Exception as e:
            # If Redis write fails, save to memory as backup
            logger.warning(f"Redis write failed, saving to memory: {e}")
    tasks_memory[task_id] = task_data

def get_task(task_id: str) -> dict:
    """Get task from Redis or memory"""
    _ensure_redis()
    if STORAGE_MODE == "redis" and redis_client is not None:
        try:
            data = redis_client.get(f"task:{task_id}")
            return json.loads(data) if data else None
        except Exception as e:
            print(f"WARNING: Redis read failed, falling back to memory: {e}")
    return tasks_memory.get(task_id)

def update_task(task_id: str, updates: dict):
    """Update task in Redis or memory"""
    task = get_task(task_id)
    if task:
        task.update(updates)
        save_task(task_id, task)

def list_tasks() -> list:
    """List all tasks from Redis or memory"""
    _ensure_redis()
    if STORAGE_MODE == "redis" and redis_client is not None:
        try:
            keys = redis_client.keys("task:*")
            tasks = []
            for key in keys[-100:]:  # Last 100 tasks
                data = redis_client.get(key)
                if data:
                    tasks.append(json.loads(data))
            return tasks
        except Exception as e:
            print(f"WARNING: Redis list failed, falling back to memory: {e}")
    return list(tasks_memory.values())[-100:]

# ==============================================================================
# ПУБЛИЧНАЯ ВЕРСИЯ - HARDCODED ПАРАМЕТРЫ
# В Pro версии эти параметры будут конфигурируемы через env переменные
# ==============================================================================

TASK_TTL_HOURS = 72  # Hardcoded в публичной версии - 3 суток (72 часа)
WEBHOOK_BACKGROUND_INTERVAL_SECONDS = 900  # 15 минут - hardcoded в публичной версии
WEBHOOK_MAX_RETRY_ATTEMPTS = 5  # Максимум попыток отправки webhook - hardcoded
WEBHOOK_RETRY_DELAY_SECONDS = 60  # Задержка между попытками webhook - hardcoded
CLEANUP_INTERVAL_SECONDS = 3600  # 1 час - hardcoded в публичной версии

def format_ttl_human(hours: int) -> str:
    """Форматирует время жизни файлов в человеко-читаемом виде"""
    if hours >= 24:
        days = hours // 24
        remaining_hours = hours % 24
        if remaining_hours == 0:
            return f"{days} day{'s' if days != 1 else ''}"
        else:
            return f"{days} day{'s' if days != 1 else ''} {remaining_hours}h"
    else:
        return f"{hours}h"

# ==============================================================================
# Конфигурация
# ==============================================================================

TASKS_DIR = "/app/tasks"
os.makedirs(TASKS_DIR, exist_ok=True)

# Recovery настройки (HARDCODED for public version)
RECOVERY_ENABLED = True  # os.getenv('RECOVERY_ENABLED', 'true').lower() in ('true', '1', 'yes')
RECOVERY_INTERVAL_MINUTES = 0  # int(os.getenv('RECOVERY_INTERVAL_MINUTES', '0'))  # 0 = только при старте
MAX_TASK_RETRIES = 3  # int(os.getenv('MAX_TASK_RETRIES', '3'))
RETRY_DELAY_SECONDS = 60  # int(os.getenv('RETRY_DELAY_SECONDS', '60'))
RECOVERY_PUBLIC_ENABLED = False  # os.getenv('RECOVERY_PUBLIC_ENABLED', 'false').lower() in ('true', '1', 'yes')

# Webhook настройки (HARDCODED for public version)
WEBHOOK_HEADERS = None  # os.getenv('WEBHOOK_HEADERS', None)  # Глобальные webhook заголовки (опционально)
DEFAULT_WEBHOOK_URL = None  # os.getenv('DEFAULT_WEBHOOK_URL', None)  # Дефолтный webhook URL (опционально)

# Вспомогательные функции для работы с задачами
def get_task_dir(task_id: str) -> str:
    """Получить директорию задачи (все файлы хранятся здесь)"""
    return os.path.join(TASKS_DIR, task_id)

def get_task_output_dir(task_id: str) -> str:
    """Получить директорию для выходных файлов задачи (совпадает с task_dir)"""
    return get_task_dir(task_id)

def create_task_dirs(task_id: str):
    """Создать директорию для задачи"""
    os.makedirs(get_task_dir(task_id), exist_ok=True)

def save_task_metadata(task_id: str, metadata: dict, verify: bool = False):
    """
    Save metadata.json for task with optional verification.
    
    Args:
        task_id: Task identifier
        metadata: Metadata dict to save
        verify: If True, read back and verify the write succeeded
    
    Returns:
        True if save succeeded (and verification passed if enabled), False otherwise
    """
    metadata_path = os.path.join(get_task_dir(task_id), "metadata.json")
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        os.chmod(metadata_path, 0o644)
        
        if verify:
            # Read back and verify
            try:
                with open(metadata_path, 'r') as f:
                    saved = json.load(f)
                if saved.get('task_id') == task_id and saved.get('status') == metadata.get('status'):
                    logger.debug(f"[{task_id}] metadata.json write verified ✓")
                    return True
                else:
                    logger.warning(f"[{task_id}] metadata.json verification failed ✗")
                    return False
            except Exception as e:
                logger.warning(f"[{task_id}] metadata.json read-back failed: {e} ✗")
                return False
        return True
    except Exception as e:
        logger.error(f"[{task_id}] Failed to save metadata.json: {e}")
        return False


def build_structured_metadata(
    task_id: str,
    status: str,
    created_at: str,
    completed_at: str | None,
    expires_at: str | None,
    video_url: str | None,
    operations: list | None,
    output_files: list | None,
    total_files: int | None,
    is_chunked: bool | None,
    metadata_url: str | None,
    metadata_url_internal: str | None,
    webhook_url: str | None,
    webhook_headers: dict | None,
    webhook_status: dict | None,
    retry_count: int | None,
    client_meta: Any | None,
    # Optional additional fields
    operations_count: int | None = None,
    total_size: int | None = None,
    total_size_mb: float | None = None,
    ttl_seconds: int | None = None,
    ttl_human: str | None = None
) -> dict:
    """
    Builds metadata object with structured, predictable field ordering.

    Field groups (in order):
    1. Task info (task_id, status, timestamps)
    2. Input (video_url, operations)
    3. Output (output_files, metadata_url, etc)
    4. Webhook (webhook object with status tracking)
    5. Client meta (always last)
    """
    result = {}

    # 1. TASK INFO
    result["task_id"] = task_id
    result["status"] = status
    result["created_at"] = created_at
    if completed_at is not None:
        result["completed_at"] = completed_at
    if expires_at is not None:
        result["expires_at"] = expires_at
    if retry_count is not None:
        result["retry_count"] = retry_count

    # 2. INPUT (original request data)
    input_data = {}
    if video_url is not None:
        input_data["video_url"] = video_url
    if operations is not None:
        input_data["operations"] = operations
    if operations_count is not None:
        input_data["operations_count"] = operations_count
    if input_data:  # Only add if not empty
        result["input"] = input_data

    # 3. OUTPUT (processing result)
    output_data = {}
    if output_files is not None:
        output_data["output_files"] = output_files
    if total_files is not None:
        output_data["total_files"] = total_files
    if total_size is not None:
        output_data["total_size"] = total_size
    if total_size_mb is not None:
        output_data["total_size_mb"] = total_size_mb
    if is_chunked is not None:
        output_data["is_chunked"] = is_chunked
    # URLs (external first if available, then internal)
    if metadata_url is not None:
        output_data["metadata_url"] = metadata_url
    if metadata_url_internal is not None:
        output_data["metadata_url_internal"] = metadata_url_internal
    if ttl_seconds is not None:
        output_data["ttl_seconds"] = ttl_seconds
    if ttl_human is not None:
        output_data["ttl_human"] = ttl_human
    if output_data:  # Only add if not empty
        result["output"] = output_data

    # 4. WEBHOOK
    if webhook_status:
        # Use existing webhook status from storage
        result["webhook"] = webhook_status
    elif webhook_url:
        # Create new webhook object
        result["webhook"] = {
            "url": webhook_url,
            "headers": webhook_headers,
            "status": "pending",
            "attempts": 0,
            "last_attempt": None,
            "last_status": None,
            "last_error": None,
            "next_retry": None,
            "task_id": task_id
        }
    else:
        result["webhook"] = None

    # 5. CLIENT META (always last)
    if client_meta is not None:
        result["client_meta"] = client_meta

    return result


def load_task_metadata(task_id: str) -> dict:
    """Загрузить metadata.json для задачи"""
    metadata_path = os.path.join(get_task_dir(task_id), "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return None

def save_webhook_state(task_id: str, state: dict):
    """Сохраняет состояние webhook в metadata.json в поле 'webhook'"""
    try:
        meta_path = os.path.join(get_task_dir(task_id), "metadata.json")
        # Читаем текущую metadata
        metadata = None
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except Exception:
                pass

        if not metadata:
            # Если metadata еще не создана, создаем минимальную структуру
            metadata = {"webhook": state}
        else:
            # Обновляем webhook объект
            metadata["webhook"] = state

        # Сохраняем обновленную metadata
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        os.chmod(meta_path, 0o644)
    except Exception as e:
        logger.debug(f"[{task_id[:8]}] Failed to save webhook state: {e}")
        pass

def load_webhook_state(task_id: str) -> dict | None:
    """Загружает состояние webhook из metadata.json поля 'webhook'"""
    try:
        meta_path = os.path.join(get_task_dir(task_id), "metadata.json")
        if not os.path.exists(meta_path):
            return None

        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        # Извлекаем webhook из metadata
        return metadata.get("webhook")
    except Exception:
        return None

# Настройка логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
try:
    _log_level = getattr(logging, LOG_LEVEL, logging.INFO)
except Exception:
    _log_level = logging.INFO
logging.basicConfig(
    level=_log_level,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_startup_info():
    """Выводит информацию о конфигурации сервиса при старте."""
    # Ещё раз попробуем инициализировать Redis (до 3 секунд),
    # чтобы поймать случаи, когда Redis поднялся чуть позже
    try:
        wait_for_redis(_ensure_redis, retries=6, delay=0.5, logger=logger)
    except Exception:
        pass
    # Сохраняем текущий форматтер
    root_logger = logging.getLogger()
    handlers = root_logger.handlers if root_logger.handlers else [logging.StreamHandler()]
    old_formatters = [h.formatter for h in handlers]
    # Устанавливаем временный форматтер без времени для всего стартового блока
    for h in handlers:
        h.setFormatter(logging.Formatter('%(message)s'))
    try:
        logger.info("=" * 60)
        logger.info("Video Processor API - PUBLIC VERSION")
        logger.info("=" * 60)
        logger.info("⚠️  PUBLIC VERSION - HARDCODED PARAMETERS")
        logger.info("")
        logger.info("📋 Configuration:")
        logger.info(f"   Workers: 2 | Redis: {REDIS_HOST}:{REDIS_PORT} (256MB) | Storage: {STORAGE_MODE}")
        logger.info(f"   TTL: {TASK_TTL_HOURS}h | Recovery: retries={MAX_TASK_RETRIES}, delay={RETRY_DELAY_SECONDS}s")
        logger.info(f"   Webhook: interval={WEBHOOK_BACKGROUND_INTERVAL_SECONDS}s, retries={WEBHOOK_MAX_RETRY_ATTEMPTS}, delay={WEBHOOK_RETRY_DELAY_SECONDS}s")
        logger.info(f"   Resender: {int(WEBHOOK_BACKGROUND_INTERVAL_SECONDS)}s | Progress: off")
        logger.info(f"   Cleanup: {CLEANUP_INTERVAL_SECONDS}s | Meta: {MAX_CLIENT_META_BYTES}B, depth={MAX_CLIENT_META_DEPTH}")
        logger.info("")
        logger.info("🚀 Upgrade to Pro: support@alexbic.net")
        logger.info("   ✓ Configurable parameters ✓ External Redis ✓ Variable TTL")
        logger.info("=" * 60)
        try:
            logger.info(f"   Log level: {LOG_LEVEL}")
        except Exception:
            pass
        # Log API access mode
        if API_KEY_ENABLED:
            if PUBLIC_BASE_URL:
                logger.info(f"   Mode: PUBLIC API | Base URL: {PUBLIC_BASE_URL}")
                logger.info("   Authentication: ENABLED")
            else:
                logger.info("   Mode: PUBLIC API (internal URLs)")
                logger.info("   Authentication: ENABLED")
        else:
            logger.info("   Mode: INTERNAL (Docker network)")
            if PUBLIC_BASE_URL:
                logger.warning("⚠️  PUBLIC_BASE_URL ignored (API_KEY not set)")
                logger.warning(f"   Set API_KEY to activate: {PUBLIC_BASE_URL}")
            logger.info("   Authentication: DISABLED")
        logger.info("=" * 60)
    finally:
        # Возвращаем старый форматтер
        for h, old_fmt in zip(handlers, old_formatters):
            h.setFormatter(old_fmt)

def _log_startup_once():
    """Логируем старт приложения один раз на контейнер (атомарный маркер в /tmp)."""
    marker = "/tmp/video_processor_api_start_logged"
    try:
        fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.close(fd)

        log_startup_info()

        # Запускаем recovery при старте (в фоновом потоке с задержкой)
        def delayed_recovery():
            import time
            time.sleep(5)  # Даем серверу запуститься
            recover_stuck_tasks()

            # Если настроена периодичность - запускаем планировщик
            if RECOVERY_INTERVAL_MINUTES > 0:
                schedule_recovery()

        recovery_thread = threading.Thread(target=delayed_recovery, daemon=True)
        recovery_thread.start()

    except FileExistsError:
        # Уже логировали в этом контейнере — пропускаем
        pass
    except Exception:
        # На всякий случай логируем, если не удалось создать маркер
        log_startup_info()

# ============================================
# CLIENT META VALIDATION LIMITS
# ============================================

# Ограничения для client_meta (HARDCODED for public version)
MAX_CLIENT_META_BYTES = 16 * 1024  # int(os.getenv('MAX_CLIENT_META_BYTES', 16 * 1024))  # 16 KB
MAX_CLIENT_META_DEPTH = 5  # int(os.getenv('MAX_CLIENT_META_DEPTH', 5))
MAX_CLIENT_META_KEYS = 200  # int(os.getenv('MAX_CLIENT_META_KEYS', 200))
MAX_CLIENT_META_STRING_LENGTH = 1000  # int(os.getenv('MAX_CLIENT_META_STRING_LENGTH', 1000))
MAX_CLIENT_META_LIST_LENGTH = 200  # int(os.getenv('MAX_CLIENT_META_LIST_LENGTH', 200))

ALLOWED_JSON_PRIMITIVES = (str, int, float, bool, type(None))

# Разрешить ли попытку распарсить вложенные JSON-строки в client_meta (HARDCODED for public version)
ALLOW_NESTED_JSON_IN_META = True  # os.getenv('ALLOW_NESTED_JSON_IN_META', 'true').lower() in ('1', 'true', 'yes')


def _try_parse_json_string(s: str):
    if not isinstance(s, str):
        return s, False
    t = s.lstrip()
    if not t:
        return s, False
    if t[0] not in ('{', '['):
        return s, False
    try:
        parsed = json.loads(s)
        return parsed, True
    except Exception:
        return s, False


def normalize_client_meta(node, depth=0, conversions_left=200):
    """Рекурсивно пытается распарсить вложенные значения-строки,
    которые выглядят как JSON (объект/массив), если это включено.
    Ограничиваем глубину и количество конверсий.
    """
    if depth > MAX_CLIENT_META_DEPTH or conversions_left <= 0:
        return node

    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            nv = normalize_client_meta(v, depth + 1, conversions_left)
            out[k] = nv
        return out
    if isinstance(node, list):
        out_list = []
        for v in node:
            out_list.append(normalize_client_meta(v, depth + 1, conversions_left))
        return out_list
    if isinstance(node, str) and ALLOW_NESTED_JSON_IN_META:
        parsed, ok = _try_parse_json_string(node)
        if ok:
            return normalize_client_meta(parsed, depth + 1, conversions_left - 1)
    return node


def _validate_meta_structure(node, depth=0, counters=None):
    if counters is None:
        counters = {'keys': 0}
    if depth > MAX_CLIENT_META_DEPTH:
        return False, f"client_meta depth exceeds {MAX_CLIENT_META_DEPTH}"

    if isinstance(node, dict):
        counters['keys'] += len(node)
        if counters['keys'] > MAX_CLIENT_META_KEYS:
            return False, f"client_meta total keys exceed {MAX_CLIENT_META_KEYS}"
        for k, v in node.items():
            if not isinstance(k, str):
                return False, "client_meta keys must be strings"
            if len(k) > MAX_CLIENT_META_STRING_LENGTH:
                return False, f"client_meta key too long (> {MAX_CLIENT_META_STRING_LENGTH})"
            ok, err = _validate_meta_structure(v, depth + 1, counters)
            if not ok:
                return ok, err
        return True, None

    if isinstance(node, list):
        if len(node) > MAX_CLIENT_META_LIST_LENGTH:
            return False, f"client_meta list too long (> {MAX_CLIENT_META_LIST_LENGTH})"
        for item in node:
            ok, err = _validate_meta_structure(item, depth + 1, counters)
            if not ok:
                return ok, err
        return True, None

    if isinstance(node, ALLOWED_JSON_PRIMITIVES):
        if isinstance(node, str) and len(node) > MAX_CLIENT_META_STRING_LENGTH:
            return False, f"client_meta string too long (> {MAX_CLIENT_META_STRING_LENGTH})"
        return True, None

    return False, "client_meta contains unsupported value type"


def validate_client_meta(client_meta):
    if client_meta is None:
        return True, None
    if not isinstance(client_meta, dict):
        return False, "client_meta must be a JSON object"

    ok, err = _validate_meta_structure(client_meta)
    if not ok:
        return False, err

    try:
        # ensure_ascii=False чтобы считать реальные байты UTF-8
        meta_bytes = json.dumps(client_meta, ensure_ascii=False).encode('utf-8')
        if len(meta_bytes) > MAX_CLIENT_META_BYTES:
            return False, f"client_meta exceeds {MAX_CLIENT_META_BYTES} bytes"
    except Exception as e:
        return False, f"client_meta serialization error: {e}"

    return True, None

# Вызов логирования после определения всех лимитов и функций — выводим один раз на контейнер

# ============================================
# INPUT DOWNLOAD + VALIDATION
# ============================================

def download_media_with_validation(url: str, dest_path: str, timeout: int = 300) -> tuple[bool, str]:
    """Скачивает контент по URL в dest_path с базовой валидацией медиа.

    Отсеивает очевидно не‑медийные ответы (HTML, JSON и т.п.),
    проверяет заголовки и сигнатуру первых байт. Записывает во временный .part
    с последующим атомарным переименованием в итоговый файл.

    Возвращает (ok, message). В случае ok=False файл не создаётся.
    """
    import requests

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; VideoProcessor/1.0; +https://alexbic.net)'
        }
        with requests.get(url, stream=True, timeout=timeout, headers=headers) as r:
            try:
                r.raise_for_status()
            except Exception as e:
                return False, f"Download failed: HTTP {r.status_code} — {e}"

            ctype = (r.headers.get('Content-Type') or '').lower()
            clength = int(r.headers.get('Content-Length') or 0)

            # Быстрый отсев по типу контента
            if ctype.startswith('text/') or 'html' in ctype or 'json' in ctype:
                # Прочитаем небольшой буфер и посмотрим на содержимое
                head = r.raw.read(4096, decode_content=True)
                text_head = head.decode('utf-8', errors='ignore')
                if '<html' in text_head.lower() or 'doctype html' in text_head.lower():
                    return False, "URL returned HTML page, not media. Pass a direct media file URL."
                if 'error' in text_head.lower() and 'youtube' in text_head.lower():
                    return False, "Upstream returned an error page, likely not a direct media URL."
                # Вернём каретку, чтобы не потерять байты
                r.raw.seek(0)

            # Минимальный разумный размер (100KB) — отсечём совсем мусор
            min_reasonable = 100 * 1024

            # Запишем во временный файл и одновременно соберём первые килобайты для сигнатуры
            first_chunk = b''
            total = 0

            tmp_path = dest_path + '.part'
            with open(tmp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=64 * 1024):
                    if not chunk:
                        continue
                    if not first_chunk:
                        first_chunk = chunk[:4096]
                    f.write(chunk)
                    total += len(chunk)

            # Если заголовок заявлял маленький размер или реально скачали слишком мало
            if clength and clength < min_reasonable:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                return False, f"Downloaded file too small ({clength} bytes). Likely not media."

            if total < min_reasonable:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                return False, f"Downloaded file too small ({total} bytes). Likely not media."

            # Базовая сигнатурная проверка: MP4/WebM/MKV/MPEG-TS
            sig = first_chunk[:64]
            sig_l = sig.lower()
            looks_html = b'<html' in sig_l or b'doctype html' in sig_l
            looks_mp4 = b'ftyp' in sig  # MP4 контейнер
            looks_webm = sig.startswith(b"\x1A\x45\xDF\xA3")  # EBML (Matroska/WebM)
            looks_ts = sig.startswith(b"\x47")  # MPEG-TS (грубая эвристика)

            if looks_html:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                return False, "Downloaded HTML, not media. Provide a direct media URL (file stream)."

            # Если тип неизвестен — всё ещё допускаем, если заявлен video/* или audio/*
            type_ok = (ctype.startswith('video/') or ctype.startswith('audio/') or 'octet-stream' in ctype)
            if not (looks_mp4 or looks_webm or looks_ts or type_ok):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                return False, "File does not look like media (unknown signature and content-type)."

            # Перемещаем во final
            os.replace(tmp_path, dest_path)
            os.chmod(dest_path, 0o644)
            return True, f"Downloaded {total} bytes"

    except Exception as e:
        # Уберём .part если остался
        try:
            if os.path.exists(dest_path + '.part'):
                os.remove(dest_path + '.part')
        except Exception:
            pass
        return False, f"Download error: {e}"

# Очистка старых файлов (старше 2 часов)
def cleanup_old_files():
    """Удаляет задачи старше 2 часов (expired) и orphaned задачи без metadata.json"""
    import time
    import shutil

    try:
        if not os.path.exists(TASKS_DIR):
            return

        cleaned_count = 0
        orphaned_count = 0
        total_size_freed = 0

        for task_id in os.listdir(TASKS_DIR):
            task_path = os.path.join(TASKS_DIR, task_id)
            if not os.path.isdir(task_path):
                continue

            metadata_path = os.path.join(task_path, 'metadata.json')

            # Вычисляем размер директории
            try:
                dir_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(task_path)
                    for filename in filenames
                )
            except Exception:
                dir_size = 0

            # Orphaned tasks (без metadata.json)
            if not os.path.exists(metadata_path):
                try:
                    shutil.rmtree(task_path, ignore_errors=True)
                    orphaned_count += 1
                    total_size_freed += dir_size
                    size_mb = dir_size / 1024 / 1024
                    logger.info(f"Removed orphaned task: {task_id[:8]} ({size_mb:.1f} MB)")
                except Exception as e:
                    logger.error(f"Failed to remove orphaned task {task_id[:8]}: {e}")
                continue

            # Expired tasks (TTL истёк на основе expires_at)
            try:
                metadata = load_task_metadata(task_id)
                if metadata:
                    expires_at = metadata.get('expires_at')
                    if expires_at:
                        try:
                            expires_dt = datetime.fromisoformat(expires_at)
                            if datetime.now() > expires_dt:
                                shutil.rmtree(task_path, ignore_errors=True)
                                cleaned_count += 1
                                total_size_freed += dir_size
                                size_mb = dir_size / 1024 / 1024
                                logger.info(f"Removed expired task: {task_id[:8]} ({size_mb:.1f} MB, expired: {expires_at})")
                        except Exception:
                            # Fallback к старому методу на основе ctime
                            current_time = time.time()
                            if current_time - os.path.getctime(task_path) > (TASK_TTL_HOURS * 3600):
                                shutil.rmtree(task_path, ignore_errors=True)
                                cleaned_count += 1
                                total_size_freed += dir_size
                                size_mb = dir_size / 1024 / 1024
                                logger.info(f"Removed expired task: {task_id[:8]} ({size_mb:.1f} MB, no expires_at)")
            except Exception as e:
                logger.debug(f"Cleanup check error for {task_id[:8]}: {e}")

        if cleaned_count > 0 or orphaned_count > 0:
            total_size_mb = total_size_freed / 1024 / 1024
            logger.info(f"Cleanup summary: {cleaned_count} expired, {orphaned_count} orphaned, {total_size_mb:.1f} MB freed")

    except Exception as e:
        logger.error(f"Cleanup error: {e}")


def _post_webhook(webhook_url: str, payload: dict, webhook_headers: dict | None, task_id: str, max_retries: int = 3):
    """
    Внутренняя функция отправки webhook с retry логикой и сохранением состояния

    Args:
        webhook_url: URL для отправки webhook
        payload: Данные для отправки (JSON)
        webhook_headers: Кастомные заголовки для конкретного webhook (приоритет выше глобальных)
        task_id: ID задачи для сохранения состояния webhook
        max_retries: Максимальное количество попыток (default: 3)
    """
    import requests
    import time

    if not webhook_url:
        logger.debug(f"[{task_id[:8]}] No webhook URL provided, skipping")
        return

    # Загружаем текущее состояние webhook или создаем новое
    webhook_state = load_webhook_state(task_id)
    if not webhook_state:
        webhook_state = {
            "url": webhook_url,
            "headers": webhook_headers or {},
            "status": "pending",
            "attempts": 0,
            "last_attempt": None,
            "last_status": None,
            "last_error": None,
            "next_retry": None
        }
    else:
        # Убеждаемся что все обязательные поля присутствуют (для обратной совместимости)
        if "attempts" not in webhook_state:
            webhook_state["attempts"] = 0
        if "last_attempt" not in webhook_state:
            webhook_state["last_attempt"] = None
        if "last_status" not in webhook_state:
            webhook_state["last_status"] = None
        if "last_error" not in webhook_state:
            webhook_state["last_error"] = None
        if "next_retry" not in webhook_state:
            webhook_state["next_retry"] = None
        if "status" not in webhook_state:
            webhook_state["status"] = "pending"

    # Подготавливаем заголовки
    headers = {"Content-Type": "application/json"}

    # Добавляем глобальные пользовательские заголовки из конфига
    if WEBHOOK_HEADERS:
        try:
            # Парсим если это строка формата "Key: Value\nKey2: Value2"
            if isinstance(WEBHOOK_HEADERS, str):
                for line in WEBHOOK_HEADERS.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        k = key.strip()
                        v = value.strip()
                        if k.lower() != 'content-type':
                            headers[k] = v
            elif isinstance(WEBHOOK_HEADERS, dict):
                for k, v in WEBHOOK_HEADERS.items():
                    if k.lower() != 'content-type':
                        headers[k] = v
        except Exception as e:
            logger.debug(f"[{task_id[:8]}] Failed to parse global WEBHOOK_HEADERS: {e}")

    # Добавляем заголовки для конкретного webhook (приоритет выше глобальных)
    if webhook_headers:
        try:
            for k, v in webhook_headers.items():
                if k.lower() != 'content-type':  # Не позволяем переопределять Content-Type
                    headers[k] = v
        except Exception as e:
            logger.debug(f"[{task_id[:8]}] Failed to apply webhook_headers: {e}")

    # Пытаемся отправить webhook
    for attempt in range(max_retries):
        try:
            webhook_state["attempts"] += 1
            webhook_state["last_attempt"] = datetime.now().isoformat()

            logger.info(f"[{task_id[:8]}] Sending webhook to {webhook_url} (attempt {attempt + 1}/{max_retries})")

            response = requests.post(
                webhook_url,
                json=payload,
                timeout=30,
                headers=headers
            )

            webhook_state["last_status"] = response.status_code
            response.raise_for_status()

            # Успешно отправлено
            webhook_state["status"] = "delivered"
            webhook_state["last_error"] = None
            webhook_state["next_retry"] = None
            save_webhook_state(task_id, webhook_state)

            logger.info(f"[{task_id[:8]}] Webhook delivered successfully (status {response.status_code})")
            return

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            webhook_state["last_error"] = error_msg
            logger.warning(f"[{task_id[:8]}] Webhook attempt {attempt + 1}/{max_retries} failed: {error_msg}")

            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                sleep_time = 2 ** attempt
                logger.info(f"[{task_id[:8]}] Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                # Все попытки провалились - вычисляем next_retry для background resender
                # Стратегия: 5 мин, 15 мин, 1 час, 4 часа, 12 часов, потом каждые 24 часа
                delays = [300, 900, 3600, 14400, 43200, 86400]
                total_attempts = webhook_state["attempts"]
                delay = delays[min(total_attempts - 1, len(delays) - 1)]
                next_retry_dt = datetime.now() + timedelta(seconds=delay)
                webhook_state["next_retry"] = next_retry_dt.isoformat()
                webhook_state["status"] = "failed"

                logger.error(f"[{task_id[:8]}] All {max_retries} webhook attempts failed. Next retry at {webhook_state['next_retry']}")

    # Сохраняем финальное состояние
    save_webhook_state(task_id, webhook_state)


def send_webhook(webhook_url: str, payload: dict, webhook_headers: dict | None = None, task_id: str = None, max_retries: int = 3) -> bool:
    """
    Отправляет webhook с retry логикой (обертка для совместимости)

    Args:
        webhook_url: URL для отправки webhook
        payload: Данные для отправки (JSON)
        webhook_headers: Кастомные заголовки (опционально)
        task_id: ID задачи для отслеживания состояния (опционально)
        max_retries: Максимальное количество попыток (default: 3)

    Returns:
        True если успешно отправлено, False если все попытки провалились
    """
    if task_id:
        _post_webhook(webhook_url, payload, webhook_headers, task_id, max_retries)
        # Проверяем был ли webhook доставлен
        state = load_webhook_state(task_id)
        return state and state.get("status") == "delivered"
    else:
        # Старый режим без отслеживания состояния
        import requests
        import time

        if not webhook_url:
            return False

        headers = {"Content-Type": "application/json"}
        if webhook_headers:
            headers.update(webhook_headers)

        for attempt in range(max_retries):
            try:
                response = requests.post(webhook_url, json=payload, timeout=30, headers=headers)
                response.raise_for_status()
                return True
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"All webhook attempts failed: {e}")
                    return False
        return False


# ============================================
# VIDEO OPERATIONS REGISTRY
# ============================================

class VideoOperation:
    """Базовый класс для операций с видео"""
    def __init__(self, name: str, required_params: list, optional_params: dict = None):
        self.name = name
        self.required_params = required_params
        self.optional_params = optional_params or {}

    def validate(self, params: dict) -> tuple[bool, str]:
        """Валидация параметров операции"""
        for param in self.required_params:
            if param not in params:
                return False, f"Missing required parameter: {param}"
        return True, ""
    
    def validate_input_file(self, input_path: str) -> tuple[bool, str]:
        """Валидация входного файла перед FFmpeg операцией"""
        if not os.path.exists(input_path):
            return False, f"Input file not found: {input_path}"
        
        file_size = os.path.getsize(input_path)
        if file_size == 0:
            return False, f"Input file is empty: {input_path}"
        
        if file_size < 1024:  # < 1KB
            return False, f"Input file too small ({file_size} bytes): {input_path}"
        
        return True, ""

    def execute(self, input_path: str, output_path: str, params: dict, additional_inputs: dict = None) -> tuple[bool, str]:
        """
        Выполнение операции (переопределяется в подклассах)

        Args:
            input_path: Путь к входному видео
            output_path: Путь к выходному видео
            params: Параметры операции
            additional_inputs: Дополнительные входные данные (аудио, изображения и т.д.)
        """
        raise NotImplementedError()


class CutVideoOperation(VideoOperation):
    """Операция нарезки видео"""
    def __init__(self):
        super().__init__(
            name="cut_video",
            required_params=["start_time", "end_time"],
            optional_params={}
        )

    def execute(self, input_path: str, output_path: str, params: dict, additional_inputs: dict = None) -> tuple[bool, str]:
        """Нарезка видео"""
        # Валидация входного файла
        valid, msg = self.validate_input_file(input_path)
        if not valid:
            return False, msg
        
        start_time = params['start_time']
        end_time = params['end_time']

        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', input_path,
            '-to', str(end_time),
            '-c', 'copy',
            '-y',
            output_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"FFmpeg error: {result.stderr}"

        return True, "Cut operation completed"


class MakeShortOperation(VideoOperation):
    """Операция конвертации в Shorts формат"""
    def __init__(self):
        super().__init__(
            name="make_short",
            required_params=[],
            optional_params={
                'start_time': None,
                'end_time': None,
                'crop_mode': 'center',
                'letterbox_config': {},
                'title': {},
                'subtitles': {},
                'generate_thumbnail': True,  # Автоматическая генерация превью
                'thumbnail_timestamp': 0.5   # Время для извлечения превью (секунды)
            }
        )

    def execute(self, input_path: str, output_path: str, params: dict, additional_inputs: dict = None) -> tuple[bool, str]:
        """Конвертация в Shorts формат (1080x1920)"""
        # Валидация входного файла
        valid, msg = self.validate_input_file(input_path)
        if not valid:
            return False, msg
        
        # Применяем значения по умолчанию
        crop_mode = params.get('crop_mode', 'center')
        start_time = params.get('start_time')
        end_time = params.get('end_time')

        # additional_inputs может содержать аудио дорожки, изображения и т.д.
        # Пока не используется в базовой реализации, но доступно для расширения
        additional_inputs = additional_inputs or {}

        # Конфигурация letterbox режима
        letterbox_config_raw = params.get('letterbox_config', {})
        letterbox_config = {
            'blur_radius': letterbox_config_raw.get('blur_radius', 20),
            'bg_scale': letterbox_config_raw.get('bg_scale', '1080:1920'),
            'fg_scale': letterbox_config_raw.get('fg_scale', '-1:1080'),
            'overlay_x': letterbox_config_raw.get('overlay_x', '(W-w)/2'),
            'overlay_y': letterbox_config_raw.get('overlay_y', '(H-h)/2')
        }

        # Обработка title (новый формат: объект с text и настройками)
        title_raw = params.get('title', {})
        title_text = title_raw.get('text', '')
        title_config = {
            'fontfile': title_raw.get('fontfile'),
            'font': title_raw.get('font'),
            'fontsize': title_raw.get('fontsize', 70),
            'fontcolor': title_raw.get('fontcolor', 'white'),
            'bordercolor': title_raw.get('bordercolor', 'black'),
            'borderw': title_raw.get('borderw', 3),
            'text_align': title_raw.get('text_align', 'center'),
            'box': title_raw.get('box', False),
            'boxcolor': title_raw.get('boxcolor', 'black@0.5'),
            'boxborderw': title_raw.get('boxborderw', 10),
            'x': title_raw.get('x', 'center'),
            'y': title_raw.get('y', 150),
            'start_time': title_raw.get('start_time', 0.5),
            'duration': title_raw.get('duration', 4),
            'fade_in': title_raw.get('fade_in', 0.5),
            'fade_out': title_raw.get('fade_out', 0.5)
        }

        # Обработка subtitles (новый формат: объект с items и настройками)
        subtitles_raw = params.get('subtitles', {})
        subtitles = subtitles_raw.get('items', [])
        subtitle_config = {
            'fontfile': subtitles_raw.get('fontfile'),
            'font': subtitles_raw.get('font'),
            'fontsize': subtitles_raw.get('fontsize', 60),
            'fontcolor': subtitles_raw.get('fontcolor', 'white'),
            'bordercolor': subtitles_raw.get('bordercolor', 'black'),
            'borderw': subtitles_raw.get('borderw', 3),
            'text_align': subtitles_raw.get('text_align', 'center'),
            'box': subtitles_raw.get('box', False),
            'boxcolor': subtitles_raw.get('boxcolor', 'black@0.5'),
            'boxborderw': subtitles_raw.get('boxborderw', 10),
            'y': subtitles_raw.get('y', 'h-200')
        }

        # Определяем фильтр обрезки
        if crop_mode == 'letterbox':
            video_filter = (
                f"[0:v]scale={letterbox_config['bg_scale']}:force_original_aspect_ratio=increase,crop=1080:1920,boxblur={letterbox_config['blur_radius']}[bg];"
                f"[0:v]scale={letterbox_config['fg_scale']}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay={letterbox_config['overlay_x']}:{letterbox_config['overlay_y']}"
            )
        elif crop_mode == 'top':
            video_filter = "crop=ih*9/16:ih:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        elif crop_mode == 'bottom':
            video_filter = "crop=ih*9/16:ih:0:ih-oh,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        else:  # center
            video_filter = "crop=ih*9/16:ih,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

        # Добавляем текстовые оверлеи если указаны
        if title_text:
            # Автоматический перенос текста заголовка
            max_chars_per_line_title = int(950 / (title_config['fontsize'] * 0.55))
            if len(title_text) > max_chars_per_line_title:
                words = title_text.split(' ')
                lines = []
                current_line = []
                current_length = 0

                for word in words:
                    word_len = len(word) + 1
                    if current_length + word_len > max_chars_per_line_title and current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = word_len
                    else:
                        current_line.append(word)
                        current_length += word_len

                if current_line:
                    lines.append(' '.join(current_line))

                title_text = '\n'.join(lines[:2])

            # Экранируем спецсимволы
            title_escaped = title_text.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'").replace(',', '\\,')

            # Вычисляем тайминги для fade эффектов
            title_start = title_config['start_time']
            title_duration = title_config['duration']
            title_fade_in = title_config['fade_in']
            title_fade_out = title_config['fade_out']
            title_end = title_start + title_duration
            fade_in_end = title_start + title_fade_in
            fade_out_start = title_end - title_fade_out

            # Формируем drawtext фильтр
            drawtext_params = [
                f"text='{title_escaped}'",
                "expansion=normal",
                f"text_align={title_config['text_align']}"
            ]

            if title_config['fontfile']:
                fontfile_escaped = title_config['fontfile'].replace(':', '\\:').replace("'", "\\'")
                drawtext_params.append(f"fontfile='{fontfile_escaped}'")
            elif title_config['font']:
                font_escaped = title_config['font'].replace(':', '\\:').replace("'", "\\'")
                drawtext_params.append(f"font='{font_escaped}'")

            drawtext_params.extend([
                f"fontsize={title_config['fontsize']}",
                f"fontcolor={title_config['fontcolor']}",
                f"bordercolor={title_config['bordercolor']}",
                f"borderw={title_config['borderw']}",
                f"x=(w-text_w)/2",
                f"y={title_config['y']}",
                f"enable='between(t\\,{title_start}\\,{title_end})'",
                f"alpha='if(lt(t\\,{fade_in_end})\\,(t-{title_start})/{title_fade_in}\\,if(gt(t\\,{fade_out_start})\\,({title_end}-t)/{title_fade_out}\\,1))'"
            ])

            # Добавляем box (плашку) если включено
            if title_config.get('box'):
                drawtext_params.append(f"box=1")
                drawtext_params.append(f"boxcolor={title_config['boxcolor']}")
                if 'boxborderw' in title_config:
                    drawtext_params.append(f"boxborderw={title_config['boxborderw']}")

            video_filter += f",drawtext={':'.join(drawtext_params)}"

        # Динамические субтитры
        if subtitles:
            for subtitle in subtitles:
                sub_text = subtitle.get('text', '')
                sub_start = subtitle.get('start', 0)
                sub_end = subtitle.get('end', 0)

                if sub_text and sub_start is not None and sub_end is not None:
                    # Автоматический перенос текста
                    max_chars_per_line = int(950 / (subtitle_config['fontsize'] * 0.55))
                    if len(sub_text) > max_chars_per_line:
                        words = sub_text.split(' ')
                        lines = []
                        current_line = []
                        current_length = 0

                        for word in words:
                            word_len = len(word) + 1
                            if current_length + word_len > max_chars_per_line and current_line:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                                current_length = word_len
                            else:
                                current_line.append(word)
                                current_length += word_len

                        if current_line:
                            lines.append(' '.join(current_line))

                        sub_text = '\n'.join(lines[:2])

                    sub_escaped = sub_text.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'").replace(',', '\\,')

                    sub_drawtext_params = [
                        f"text='{sub_escaped}'",
                        "expansion=normal",
                        f"text_align={subtitle_config['text_align']}"
                    ]

                    if subtitle_config['fontfile']:
                        subfontfile_escaped = subtitle_config['fontfile'].replace(':', '\\:').replace("'", "\\'")
                        sub_drawtext_params.append(f"fontfile='{subfontfile_escaped}'")
                    elif subtitle_config['font']:
                        subfont_escaped = subtitle_config['font'].replace(':', '\\:').replace("'", "\\'")
                        sub_drawtext_params.append(f"font='{subfont_escaped}'")

                    sub_drawtext_params.extend([
                        f"fontsize={subtitle_config['fontsize']}",
                        f"fontcolor={subtitle_config['fontcolor']}",
                        f"bordercolor={subtitle_config['bordercolor']}",
                        f"borderw={subtitle_config['borderw']}",
                        f"x=(w-text_w)/2",
                        f"y={subtitle_config['y']}",
                        f"enable='between(t\\,{sub_start}\\,{sub_end})'"
                    ])

                    # Добавляем box (плашку) для субтитров если включено
                    if subtitle_config.get('box'):
                        sub_drawtext_params.append(f"box=1")
                        sub_drawtext_params.append(f"boxcolor={subtitle_config['boxcolor']}")
                        if subtitle_config.get('boxborderw'):
                            sub_drawtext_params.append(f"boxborderw={subtitle_config['boxborderw']}")

                    video_filter += f",drawtext={':'.join(sub_drawtext_params)}"

        # Выполняем FFmpeg команду
        cmd = ['ffmpeg']
        
        # Добавляем таймкоды для нарезки если указаны
        if start_time is not None:
            cmd.extend(['-ss', str(start_time)])
        
        cmd.extend(['-i', input_path])
        
        # Добавляем конечный таймкод или длительность
        if end_time is not None:
            if start_time is not None:
                # Если есть start и end - вычисляем duration
                if isinstance(start_time, (int, float)) and isinstance(end_time, (int, float)):
                    duration = end_time - start_time
                    cmd.extend(['-t', str(duration)])
                else:
                    # Для строковых таймкодов используем -to
                    cmd.extend(['-to', str(end_time)])
            else:
                cmd.extend(['-to', str(end_time)])
        
        cmd.extend([
            '-filter_complex' if crop_mode == 'letterbox' else '-vf', video_filter,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"FFmpeg error: {result.stderr}"

        # Генерация превью если включено
        thumbnail_path = None
        if params.get('generate_thumbnail', True):
            thumbnail_timestamp = params.get('thumbnail_timestamp', 0.5)
            thumbnail_path = output_path.replace('.mp4', '_thumbnail.jpg')

            thumbnail_cmd = [
                'ffmpeg',
                '-ss', str(thumbnail_timestamp),
                '-i', output_path,
                '-vframes', '1',
                '-q:v', '2',  # Высокое качество JPEG (2-5 диапазон)
                '-y',
                thumbnail_path
            ]

            thumbnail_result = subprocess.run(thumbnail_cmd, capture_output=True, text=True)
            if thumbnail_result.returncode == 0 and os.path.exists(thumbnail_path):
                logger.info(f"Generated thumbnail: {os.path.basename(thumbnail_path)} at {thumbnail_timestamp}s")
            else:
                logger.warning(f"Failed to generate thumbnail: {thumbnail_result.stderr}")
                thumbnail_path = None

        # Возвращаем список файлов (видео + превью если создано)
        output_list = [output_path]
        if thumbnail_path and os.path.exists(thumbnail_path):
            output_list.append(thumbnail_path)
            return True, f"Converted to Shorts format (1080x1920) with thumbnail", output_list
        else:
            return True, "Converted to Shorts format (1080x1920)", output_list


class ExtractAudioOperation(VideoOperation):
    """Операция извлечения аудио с поддержкой chunking для Whisper API"""
    def __init__(self):
        super().__init__(
            name="extract_audio",
            required_params=[],
            optional_params={
                'format': 'mp3',
                'bitrate': '192k',
                'chunk_duration_minutes': None,  # Длительность чанка в минутах (опционально)
                'max_chunk_size_mb': 24,         # Максимальный размер чанка в МБ (для Whisper API)
                'optimize_for_whisper': False    # Оптимизация для Whisper (16kHz, mono, 64k bitrate)
            }
        )

    def execute(self, input_path: str, output_path: str, params: dict, additional_inputs: dict = None) -> tuple[bool, str, str]:
        """Извлечение аудио из видео с опциональным chunking для Whisper API"""
        # Валидация входного файла
        valid, msg = self.validate_input_file(input_path)
        if not valid:
            return False, msg, input_path
        
        audio_format = params.get('format', 'mp3')
        bitrate = params.get('bitrate', '192k')
        chunk_duration_minutes = params.get('chunk_duration_minutes')
        max_chunk_size_mb = params.get('max_chunk_size_mb', 24)
        optimize_for_whisper = params.get('optimize_for_whisper', False)

        # Генерируем собственное имя для аудиофайла в той же директории
        output_dir = os.path.dirname(output_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_audio = os.path.join(output_dir, f"audio_{timestamp}.{audio_format}")

        # Извлекаем полное аудио
        if optimize_for_whisper:
            # Оптимизация для Whisper API
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vn',
                '-acodec', 'libmp3lame',
                '-ar', '16000',  # 16kHz sample rate (оптимально для речи)
                '-ac', '1',      # Моно
                '-b:a', '64k',   # Низкий битрейт
                '-y',
                output_audio
            ]
        else:
            # Стандартное извлечение
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-vn',
                '-acodec', 'libmp3lame' if audio_format == 'mp3' else 'aac',
                '-b:a', bitrate,
                '-y',
                output_audio
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"FFmpeg error: {result.stderr}", output_audio

        os.chmod(output_audio, 0o644)
        file_size = os.path.getsize(output_audio)
        file_size_mb = file_size / (1024 * 1024)

        # Получаем длительность аудио
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            output_audio
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        
        if probe_result.returncode != 0:
            return False, f"FFprobe error: {probe_result.stderr}", output_audio
            
        total_duration = float(probe_result.stdout.strip())

        # Проверяем нужно ли разбивать на чанки
        if chunk_duration_minutes or file_size_mb > max_chunk_size_mb:
            # Определяем длительность чанка
            if chunk_duration_minutes:
                chunk_duration_seconds = chunk_duration_minutes * 60
            else:
                # Автоматически вычисляем длительность чанка
                chunk_duration_seconds = (max_chunk_size_mb / file_size_mb) * total_duration * 0.95  # 5% запас

            logger.info(f"Splitting audio into chunks of {chunk_duration_seconds/60:.1f} minutes")

            # Разбиваем на чанки
            chunk_start = 0
            chunk_index = 0
            chunk_files = []  # список ПОЛНЫХ путей к файлам чанков

            while chunk_start < total_duration:
                chunk_end = min(chunk_start + chunk_duration_seconds, total_duration)
                chunk_filename = f"audio_{timestamp}_chunk{chunk_index:03d}.{audio_format}"
                chunk_path = os.path.join(output_dir, chunk_filename)

                # Извлекаем чанк
                if optimize_for_whisper:
                    chunk_cmd = [
                        'ffmpeg',
                        '-i', output_audio,
                        '-ss', str(chunk_start),
                        '-t', str(chunk_end - chunk_start),
                        '-acodec', 'libmp3lame',
                        '-ar', '16000',  # 16kHz
                        '-ac', '1',      # Моно
                        '-b:a', '64k',   # Низкий bitrate
                        '-y',
                        chunk_path
                    ]
                else:
                    chunk_cmd = [
                        'ffmpeg',
                        '-i', output_audio,
                        '-ss', str(chunk_start),
                        '-t', str(chunk_end - chunk_start),
                        '-acodec', 'libmp3lame' if audio_format == 'mp3' else 'aac',
                        '-b:a', bitrate,
                        '-y',
                        chunk_path
                    ]

                chunk_result = subprocess.run(chunk_cmd, capture_output=True, text=True)
                
                if chunk_result.returncode != 0:
                    logger.error(f"Chunk {chunk_index} error: {chunk_result.stderr}")
                    chunk_start = chunk_end
                    chunk_index += 1
                    continue

                os.chmod(chunk_path, 0o644)
                # сохраняем полный путь, чтобы pipeline и metadata могли корректно обработать
                chunk_files.append(chunk_path)
                
                chunk_start = chunk_end
                chunk_index += 1

            # Удаляем полный аудиофайл, оставляем только чанки
            if os.path.exists(output_audio):
                os.remove(output_audio)

            logger.info(f"Created {len(chunk_files)} chunks")

            # Возвращаем список полных путей к чанкам
            return True, f"Audio extracted and split into {len(chunk_files)} chunks", chunk_files

        else:
            # Файл не требует разбиения
            return True, f"Audio extracted to {audio_format}", output_audio


# Регистрация всех операций
OPERATIONS_REGISTRY = {
    'cut_video': CutVideoOperation(),
    'make_short': MakeShortOperation(),
    'extract_audio': ExtractAudioOperation(),
}

# Вызов логирования после определения всех параметров — выводим один раз на контейнер
_log_startup_once()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (не требует авторизации)"""
    return jsonify({
        "status": "healthy",
        "service": "video-processor-api",
        "version": "public",
        "storage_mode": STORAGE_MODE,
        "redis_available": STORAGE_MODE == "redis",
        "api_key_enabled": API_KEY_ENABLED,
        "timestamp": datetime.now().isoformat(),
        
        # Hardcoded configuration (Public Version)
        # Upgrade to Pro for configurable parameters via environment variables
        "config": {
            "workers": 2,  # Hardcoded in Dockerfile
            "redis": {
                "host": REDIS_HOST,
                "port": REDIS_PORT,
                "db": REDIS_DB,
                "maxmemory": "256MB",
                "embedded": True
            },
            "limits": {
                "task_ttl_hours": TASK_TTL_HOURS,
                "max_client_meta_bytes": MAX_CLIENT_META_BYTES,
                "max_client_meta_depth": MAX_CLIENT_META_DEPTH,
                "max_client_meta_keys": MAX_CLIENT_META_KEYS,
                "max_client_meta_string_length": MAX_CLIENT_META_STRING_LENGTH,
                "max_client_meta_list_length": MAX_CLIENT_META_LIST_LENGTH,
                "allow_nested_json_in_meta": ALLOW_NESTED_JSON_IN_META
            },
            "recovery": {
                "enabled": RECOVERY_ENABLED,
                "interval_minutes": RECOVERY_INTERVAL_MINUTES,
                "max_retries": MAX_TASK_RETRIES,
                "retry_delay_seconds": RETRY_DELAY_SECONDS,
                "public_recovery_enabled": RECOVERY_PUBLIC_ENABLED
            },
            "webhook": {
                "background_interval_seconds": WEBHOOK_BACKGROUND_INTERVAL_SECONDS,
                "max_retry_attempts": WEBHOOK_MAX_RETRY_ATTEMPTS,
                "retry_delay_seconds": WEBHOOK_RETRY_DELAY_SECONDS,
                "default_url": DEFAULT_WEBHOOK_URL,
                "global_headers": WEBHOOK_HEADERS
            },
            "cleanup": {
                "interval_seconds": CLEANUP_INTERVAL_SECONDS
            }
        },
        
        "pro_features": {
            "available": False,
            "upgrade_info": "Contact for Pro version with configurable parameters",
            "features": [
                "Configurable workers (1-10+)",
                "External Redis support",
                "Configurable task TTL (1h - 90 days)",
                "Custom webhook intervals and retries",
                "Custom recovery intervals",
                "Custom cleanup intervals",
                "Adjustable client_meta limits",
                "Priority support"
            ]
        }
    })

@app.route('/fonts', methods=['GET'])
@require_api_key
def list_fonts():
    """
    Получить список доступных шрифтов (предустановленных)
    Только встроенные шрифты. Кастомные шрифты - только в PRO версии.
    """
    try:
        # Предустановленные шрифты (встроенные в контейнер)
        # Включает игровые шрифты из gaming templates + системные шрифты
        system_fonts_list = [
            # Игровые шрифты (из gaming templates v3)
            {"name": "Russo One", "family": "display", "file": "/usr/share/fonts/truetype/custom/RussoOne-Regular.ttf"},
            {"name": "Montserrat", "family": "sans-serif", "file": "/usr/share/fonts/truetype/montserrat/Montserrat-Regular.ttf"},
            {"name": "Montserrat Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf"},
            {"name": "PT Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/custom/PTSans-Regular.ttf"},
            {"name": "PT Sans Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/custom/PTSans-Bold.ttf"},
            {"name": "Oswald", "family": "condensed", "file": "/usr/share/fonts/truetype/custom/Oswald-Regular.ttf"},
            {"name": "Oswald Bold", "family": "condensed", "file": "/usr/share/fonts/truetype/custom/Oswald-Bold.ttf"},
            {"name": "Fixel Display", "family": "geometric", "file": "/usr/share/fonts/truetype/custom/FixelDisplay-Regular.ttf"},
            {"name": "Fixel Text", "family": "geometric", "file": "/usr/share/fonts/truetype/custom/FixelText-Regular.ttf"},

            # Системные шрифты
            {"name": "DejaVu Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"},
            {"name": "DejaVu Sans Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"},
            {"name": "DejaVu Serif", "family": "serif", "file": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"},
            {"name": "Liberation Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"},
            {"name": "Liberation Sans Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"},
            {"name": "Liberation Serif", "family": "serif", "file": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"},
            {"name": "Liberation Mono", "family": "monospace", "file": "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"},
            {"name": "Noto Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"},
            {"name": "Roboto", "family": "sans-serif", "file": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf"},
            {"name": "Roboto Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf"},
            {"name": "Open Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf"},
            {"name": "Open Sans Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf"}
        ]

        # Фильтруем только существующие шрифты
        available_fonts = []
        for font in system_fonts_list:
            if os.path.exists(font["file"]):
                available_fonts.append(font)

        return jsonify({
            "status": "success",
            "total_fonts": len(available_fonts),
            "fonts": available_fonts,
            "note": "Custom fonts upload available in PRO version only"
        })

    except Exception as e:
        logger.error(f"Error listing fonts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<path:file_path>', methods=['GET'])
def download_file(file_path):
    """Скачать файл из задачи (не требует авторизации - доступ по task_id)

    Поддерживаемые форматы:
    - /download/{task_id}/{filename}
    - /download/{task_id}/metadata.json
    """
    try:
        full_path = os.path.join(TASKS_DIR, file_path)
        
        # Проверка безопасности - файл должен быть внутри TASKS_DIR
        if not os.path.abspath(full_path).startswith(os.path.abspath(TASKS_DIR)):
            return jsonify({"status": "error", "error": "Invalid file path"}), 403
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            # conditional=True позволяет поддерживать диапазоны (Range) и эффективное кеширование
            return send_file(full_path, as_attachment=True, conditional=True)
        else:
            return jsonify({"status": "error", "error": "File not found"}), 404
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================
# АСИНХРОННАЯ ОБРАБОТКА
# ============================================

@app.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get task status (no auth required - task_id is unique).
    
    Priority (Redis-first architecture):
    1. Redis cache (< 1ms, TTL 72h) - fastest, always fresh
    2. metadata.json on disk (5ms, persistent) - reliable fallback after Redis expires
    3. Task directory exists check - minimal info for in-progress tasks
    4. 404 - task not found
    """
    try:
        # PRIORITY 1: Try Redis first (fastest, within TTL)
        _ensure_redis()
        task = None
        if STORAGE_MODE == "redis" and redis_client is not None:
            try:
                data = redis_client.get(f"task:{task_id}")
                if data:
                    task = json.loads(data)
                    logger.debug(f"[{task_id[:8]}] /task_status: cache HIT (Redis), status={task.get('status')}")
            except Exception as e:
                logger.debug(f"[{task_id[:8]}] Redis read failed: {e}")

        if task:
            # Redis содержит актуальные данные синхронизированные с metadata.json
            status = task.get('status')
            
            # Для всех статусов возвращаем данные из Redis
            if status in ['queued', 'processing']:
                # Задачи в процессе - минимальный статус
                return jsonify({
                    "task_id": task_id,
                    "status": status,
                    "created_at": task.get('created_at'),
                    "progress": task.get('progress', 0)
                })
            
            if status == 'completed':
                # Завершённые задачи - полная структура из Redis
                # (синхронизирована с metadata.json при завершении)
                return jsonify(task.get('metadata', task))
            
            if status == 'error':
                # Ошибки - полная структура из Redis
                return jsonify(task.get('metadata', task))
            
            # Fallback для неизвестных статусов
            return jsonify(task)

        # PRIORITY 2: Fallback to metadata.json (persistent, source of truth)
        logger.debug(f"[{task_id[:8]}] /task_status: cache MISS (Redis), checking disk")
        metadata = load_task_metadata(task_id)
        if metadata:
            logger.info(f"[{task_id[:8]}] /task_status: returning from disk (Redis TTL expired or unavailable)")
            # Return metadata as-is (already has input/output structure)
            return jsonify(metadata)

        # PRIORITY 3: Check if task directory exists (in-progress without metadata yet)
        if os.path.isdir(get_task_dir(task_id)):
            logger.warning(f"[{task_id[:8]}] /task_status: task directory exists but no data (Redis/disk issue)")
            try:
                created_at = datetime.fromtimestamp(os.path.getctime(get_task_dir(task_id))).isoformat()
            except Exception:
                created_at = None
            
            return jsonify({
                "task_id": task_id,
                "status": "processing",
                "created_at": created_at
            })

        # PRIORITY 4: Task not found
        logger.warning(f"[{task_id[:8]}] /task_status: task not found (no Redis, no metadata.json, no directory)")
        return jsonify({"error": "Task not found"}), 404

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/tasks', methods=['GET'])
@require_api_key
def list_all_tasks():
    """Получить список всех задач"""
    try:
        recent_tasks = list_tasks()
        # Перестроим задачи так, чтобы client_meta оказался внизу (если есть)
        normalized = []
        for t in recent_tasks:
            if not isinstance(t, dict):
                normalized.append(t)
                continue
            cm = t.pop('client_meta', None)
            ordered = {
                k: t[k] for k in t.keys()
            }
            if cm is not None:
                ordered['client_meta'] = cm
            normalized.append(ordered)

        return jsonify({
            "total": len(normalized),
            "tasks": normalized,
            "storage_mode": STORAGE_MODE
        })
    except Exception as e:
        logger.error(f"List tasks error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/process_video', methods=['POST'])
@require_api_key
def process_video():
    """
    Endpoint для обработки видео

    Поддерживает:
    - Pipeline обработки (цепочка операций: cut, to_shorts, extract_audio)
    - Sync/Async режимы
    - Webhook уведомления после завершения

    Пример запроса:
    {
      "video_url": "https://...",
      "execution": "sync",  # или "async"
      "operations": [
        {"type": "cut", "start_time": "00:00:10", "end_time": "00:00:20"},
        {"type": "to_shorts", "letterbox_config": {...}, "title": {...}}
      ],
      "webhook_url": "https://..." # опционально
    }
    """
    try:
        cleanup_old_files()

        data = request.json
        if not data:
            return jsonify({"status": "error", "error": "JSON data required"}), 400

        # Базовые параметры
        video_url = data.get('video_url')
        execution = data.get('execution', 'sync')  # sync или async
        operations = data.get('operations', [])

        # Webhook - только новый формат (объект с url и headers)
        webhook = data.get('webhook')
        webhook_url = None
        webhook_headers = None

        if webhook is not None:
            # Принимаем только объект формата: {"url": "...", "headers": {...}}
            if not isinstance(webhook, dict):
                return jsonify({"error": "Invalid webhook (must be an object with 'url' and optional 'headers')"}), 400

            webhook_url = webhook.get('url')
            webhook_headers = webhook.get('headers')

            # Валидация webhook.url
            if webhook_url is not None:
                if not isinstance(webhook_url, str) or not webhook_url.lower().startswith(("http://", "https://")):
                    return jsonify({"error": "Invalid webhook.url (must start with http(s)://)"}), 400
                if len(webhook_url) > 2048:
                    return jsonify({"error": "Invalid webhook.url (too long)"}), 400

            # Валидация webhook.headers
            if webhook_headers is not None:
                if not isinstance(webhook_headers, dict):
                    return jsonify({"error": "Invalid webhook.headers (must be an object)"}), 400
                for key, value in webhook_headers.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        return jsonify({"error": "Invalid webhook.headers (keys and values must be strings)"}), 400
                    if len(key) > 256 or len(value) > 2048:
                        return jsonify({"error": "Invalid webhook.headers (header name or value too long)"}), 400

        # Fallback на DEFAULT_WEBHOOK_URL если webhook не указан
        if webhook_url is None and DEFAULT_WEBHOOK_URL:
            webhook_url = DEFAULT_WEBHOOK_URL

        # Произвольные метаданные клиента для сквозного возврата в ответах/вебхуках
        client_meta = data.get('client_meta')
        if client_meta is None and 'meta' in data:
            # Поддержка алиаса 'meta' для совместимости
            client_meta = data.get('meta')

        # Если client_meta пришёл строкой, пытаемся распарсить как JSON-объект
        if isinstance(client_meta, str):
            try:
                # Сначала проверим грубый лимит размера строки до парсинга
                if len(client_meta.encode('utf-8')) > MAX_CLIENT_META_BYTES:
                    return jsonify({
                        "status": "error",
                        "error": f"Invalid client_meta: exceeds {MAX_CLIENT_META_BYTES} bytes"
                    }), 400
                parsed = json.loads(client_meta)
                if not isinstance(parsed, dict):
                    return jsonify({
                        "status": "error",
                        "error": "Invalid client_meta: must be an object or JSON stringified object"
                    }), 400
                client_meta = parsed
            except json.JSONDecodeError as e:
                return jsonify({
                    "status": "error",
                    "error": f"Invalid client_meta: JSON parse error ({str(e)})"
                }), 400

        # Пытаемся распарсить вложенные JSON-строки (вроде {{ $json.metadata.toJsonString() }})
        if isinstance(client_meta, (dict, list)):
            client_meta = normalize_client_meta(client_meta)

        # Валидация client_meta с ограничениями
        ok, err = validate_client_meta(client_meta)
        if not ok:
            return jsonify({
                "status": "error",
                "error": f"Invalid client_meta: {err}"
            }), 400

        if not video_url:
            return jsonify({"status": "error", "error": "video_url is required"}), 400

        if not operations:
            return jsonify({
                "status": "error",
                "error": "operations list is required"
            }), 400

        # Валидация операций
        for op in operations:
            op_type = op.get('type')
            if not op_type:
                return jsonify({
                    "status": "error",
                    "error": "Each operation must have 'type' field"
                }), 400

            if op_type not in OPERATIONS_REGISTRY:
                return jsonify({
                    "status": "error",
                    "error": f"Unknown operation type: {op_type}. Available: {list(OPERATIONS_REGISTRY.keys())}"
                }), 400

            # Валидация параметров операции
            operation_handler = OPERATIONS_REGISTRY[op_type]
            is_valid, error_msg = operation_handler.validate(op)
            if not is_valid:
                return jsonify({
                    "status": "error",
                    "error": f"Operation '{op_type}' validation failed: {error_msg}"
                }), 400

        # Выполнение операций
        if execution == 'async':
            # Асинхронный режим
            task_id = str(uuid.uuid4())
            
            # Создаем директории для задачи
            create_task_dirs(task_id)
            
            now = datetime.now()
            task_data = {
                'task_id': task_id,
                'status': 'queued',
                'progress': 0,
                'video_url': video_url,
                'operations': operations,
                'client_meta': client_meta,
                'created_at': now.isoformat(),
                'expires_at': (now + timedelta(hours=TASK_TTL_HOURS)).isoformat(),
                'retry_count': 0,
                'last_retry_at': None
            }
            save_task(task_id, task_data)

            # Сохраняем начальные метаданные на диск для механизма recovery
            initial_metadata = build_structured_metadata(
                task_id=task_id,
                status='queued',
                created_at=task_data['created_at'],
                completed_at=None,
                expires_at=task_data['expires_at'],
                video_url=video_url,
                operations=operations,
                output_files=[],
                total_files=0,
                is_chunked=False,
                metadata_url=None,
                metadata_url_internal=None,
                webhook_url=webhook.get('url') if webhook else None,
                webhook_headers=webhook.get('headers') if webhook else None,
                webhook_status=webhook if webhook else None,
                retry_count=0,
                client_meta=client_meta,
                operations_count=len(operations),
                total_size=0,
                total_size_mb=0.0,
                ttl_seconds=TASK_TTL_HOURS * 3600,
                ttl_human=format_ttl_human(TASK_TTL_HOURS)
            )
            save_task_metadata(task_id, initial_metadata)

            # Запускаем фоновую обработку
            thread = threading.Thread(
                target=process_video_pipeline_background,
                args=(task_id, video_url, operations, webhook)
            )
            thread.daemon = True
            thread.start()

            logger.info(f"Task created (async): {task_id} | {video_url} | operations={len(operations)}")

            resp = {
                "task_id": task_id,
                "status": "processing",
                "message": "Task created and processing in background",
                "check_status_url": build_absolute_url(f"/task_status/{task_id}")
            }
            # Добавляем webhook объект, если был предоставлен
            if webhook:
                resp["webhook"] = webhook
            # client_meta всегда в конце
            if client_meta is not None:
                resp["client_meta"] = client_meta
            return jsonify(resp), 202

        else:
            # Синхронный режим
            task_id = str(uuid.uuid4())
            logger.info(f"Task created (sync): {task_id} | {video_url} | operations={len(operations)}")

            # Создаем директории для задачи
            create_task_dirs(task_id)

            return process_video_pipeline_sync(task_id, video_url, operations, webhook, client_meta)

    except Exception as e:
        logger.error(f"Process video error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


def process_video_pipeline_sync(task_id: str, video_url: str, operations: list, webhook: dict = None, client_meta: dict | None = None) -> dict:
    """Синхронное выполнение pipeline операций"""

    # Создаем начальную задачу в Redis для возможности update_task позже
    now = datetime.now()
    initial_task = {
        'task_id': task_id,
        'status': 'processing',
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(hours=TASK_TTL_HOURS)).isoformat()
    }
    save_task(task_id, initial_task)

    # Извлекаем webhook_url и webhook_headers из webhook объекта
    webhook_url = None
    webhook_headers = None
    if webhook:
        webhook_url = webhook.get('url')
        webhook_headers = webhook.get('headers')

    # Скачиваем исходное видео в input/ с валидацией
    input_filename = f"{uuid.uuid4()}.mp4"
    input_path = os.path.join(get_task_dir(task_id), f"input_{input_filename}")

    ok, msg = download_media_with_validation(video_url, input_path)
    if not ok:
        logger.error(f"Task {task_id}: download validation failed — {msg}")
        return jsonify({
            "status": "error",
            "error": msg,
            "task_id": task_id
        }), 400

    current_input = input_path
    output_files = []  # Список всех созданных output файлов

    # Логируем создание задачи
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"[{now}] ✨ Задача создана: [{task_id}] | SYNC | Подзадач {len(operations)}")
    
    # Выполняем операции последовательно
    for idx, op_data in enumerate(operations):
        op_type = op_data['type']
        operation = OPERATIONS_REGISTRY[op_type]

        # Генерируем временный выходной файл
        if idx == len(operations) - 1:
            # Последняя операция - финальный файл с семантическим префиксом
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Определяем префикс в зависимости от типа операции
            if op_type == 'make_short':
                prefix = 'short'
            elif op_type == 'cut_video':
                prefix = 'video'
            elif op_type == 'extract_audio':
                prefix = 'audio'  # хотя extract_audio сам формирует имя
            else:
                prefix = 'processed'
            
            output_filename = f"{prefix}_{timestamp}.mp4"
            output_path = os.path.join(get_task_dir(task_id), output_filename)
        else:
            # Промежуточный файл
            output_path = os.path.join(get_task_dir(task_id), f"temp_{idx}_{uuid.uuid4()}.mp4")

        # Логируем начало операции
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"[{now}] [{task_id[:8]}] 🚀 Обработка: {op_type} [{idx+1}/{len(operations)}]")
        op_start_time = datetime.now()

        # Выполняем операцию
        result = operation.execute(current_input, output_path, op_data)
        
        # Вычисляем время выполнения операции
        op_duration = (datetime.now() - op_start_time).total_seconds()
        
        # Обрабатываем результат (может быть 2 или 3 значения)
        if len(result) == 3:
            success, message, actual_output = result
            # Если операция вернула другой путь (например extract_audio создал .mp3 или чанки)
            if actual_output:
                if isinstance(actual_output, list):
                    # Список файлов (например чанки)
                    output_files.extend(actual_output)
                    output_path = actual_output[0] if actual_output else output_path
                elif actual_output != output_path:
                    output_path = actual_output
        else:
            success, message = result

        if not success:
            # Create error metadata with full structure
            now = datetime.now()
            error_metadata = build_structured_metadata(
                task_id=task_id,
                status="error",
                created_at=now.isoformat(),
                completed_at=now.isoformat(),
                expires_at=(now + timedelta(hours=TASK_TTL_HOURS)).isoformat(),
                video_url=video_url,
                operations=operations,
                output_files=[],
                total_files=0,
                is_chunked=False,
                metadata_url=None,
                metadata_url_internal=None,
                webhook_url=webhook_url if webhook else None,
                webhook_headers=webhook_headers if webhook else None,
                webhook_status=None,
                retry_count=0,
                client_meta=client_meta,
                operations_count=len(operations),
                total_size=0,
                total_size_mb=0.0,
                ttl_seconds=TASK_TTL_HOURS * 3600,
                ttl_human=format_ttl_human(TASK_TTL_HOURS)
            )
            error_metadata["error"] = message
            error_metadata["failed_at"] = now.isoformat()
            
            # Save error metadata
            save_task_metadata(task_id, error_metadata)
            
            # Sync to Redis
            try:
                update_task(task_id, {
                    "status": "error",
                    "metadata": error_metadata
                })
            except Exception:
                pass
            
            return jsonify(error_metadata), 400
        
        # Сохраняем output файл если это последняя операция
        if idx == len(operations) - 1:
            if not output_files:  # Если операция не вернула список файлов
                output_files.append(output_path)

        # Удаляем предыдущий временный файл
        if current_input != input_path and os.path.exists(current_input):
            os.remove(current_input)

        # Следующая операция будет использовать этот файл как вход
        current_input = output_path

    # Удаляем временные файлы
    import shutil
    task_dir = get_task_dir(task_id)
    
    # Удаляем входные и временные файлы по префиксу
    if os.path.exists(task_dir):
        for filename in os.listdir(task_dir):
            if filename.startswith('input_') or filename.startswith('temp_'):
                file_path = os.path.join(task_dir, filename)
                try:
                    os.remove(file_path)
                    logger.info(f"Task {task_id}: Deleted temporary file: {filename}")
                except Exception as e:
                    logger.warning(f"Task {task_id}: Failed to delete {filename}: {e}")

    # Собираем информацию о всех output файлах
    files_info = []
    total_size = 0

    # Построение карты chunk-информации по шаблону имени *_chunkNNN.ext
    pattern = re.compile(r"^(?P<prefix>.+)_chunk(?P<index>\d{3})\.(?P<ext>[^.]+)$")
    chunk_groups = {}
    for p in output_files:
        fname = os.path.basename(p)
        m = pattern.match(fname)
        if m:
            prefix = m.group('prefix')
            idx = int(m.group('index'))
            chunk_groups.setdefault(prefix, []).append((fname, idx))
    chunk_map = {}
    for prefix, lst in chunk_groups.items():
        total = len(lst)
        for fname, idx in lst:
            chunk_map[fname] = {
                'chunk': f"{idx + 1}:{total}"
            }
    for file_path in output_files:
        if os.path.exists(file_path):
            os.chmod(file_path, 0o644)
            file_size = os.path.getsize(file_path)
            total_size += file_size
            filename = os.path.basename(file_path)
            download_path = f"/download/{task_id}/{filename}"
            
            entry = {
                "filename": filename,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "download_path": download_path,
                "download_url_internal": build_internal_url_background(download_path)
            }
            # Добавляем download_url только если есть публичный URL (API_KEY + PUBLIC_BASE_URL)
            if API_KEY_ENABLED and PUBLIC_BASE_URL:
                entry["download_url"] = build_absolute_url_background(download_path)
            if filename in chunk_map:
                entry.update(chunk_map[filename])
            files_info.append(entry)

    # Красивое логирование результатов
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for file_info in files_info:
        filename = file_info.get('filename', '')
        file_size = file_info.get('file_size_mb', 0)
        
        if filename.endswith('.mp4'):
            # Видео (основной файл или cut_video)
            if '_thumbnail' not in filename:
                logger.info(f"[{now}] [{task_id[:8]}] 🎬 Видео готово: {file_size} MB")
        elif filename.endswith(('.mp3', '.wav', '.aac', '.flac')):
            # Аудио (extract_audio)
            logger.info(f"[{now}] [{task_id[:8]}] 🎵 Аудио готово: {file_size} MB")
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            # Изображение (превью)
            logger.info(f"[{now}] [{task_id[:8]}] 🖼️ Превью создано: {file_size} MB")
        else:
            # Другие файлы
            logger.info(f"[{now}] [{task_id[:8]}] 📁 Файл готов: {filename} ({file_size} MB)")

    # Сохраняем metadata
    now = datetime.now()
    expires_at_iso = (now + timedelta(hours=TASK_TTL_HOURS)).isoformat()
    is_chunked = any(f.get('chunk') for f in files_info)
    
    # Добавляем expires_at к каждому файлу
    for file_entry in files_info:
        file_entry["expires_at"] = expires_at_iso
    metadata = build_structured_metadata(
        task_id=task_id,
        status="completed",
        created_at=now.isoformat(),
        completed_at=now.isoformat(),
        expires_at=expires_at_iso,
        video_url=video_url,
        operations=operations,
        output_files=files_info,
        total_files=len(files_info),
        is_chunked=is_chunked,
        metadata_url=build_absolute_url_background(f"/download/{task_id}/metadata.json") if (PUBLIC_BASE_URL and API_KEY) else None,
        metadata_url_internal=build_internal_url_background(f"/download/{task_id}/metadata.json"),
        webhook_url=webhook_url,
        webhook_headers=webhook_headers,
        webhook_status=None,
        retry_count=0,
        client_meta=client_meta,
        operations_count=len(operations),
        total_size=total_size,
        total_size_mb=round(total_size / (1024 * 1024), 2),
        ttl_seconds=TASK_TTL_HOURS * 3600,
        ttl_human=format_ttl_human(TASK_TTL_HOURS)
    )
    
    # Save metadata.json (source of truth)
    save_task_metadata(task_id, metadata)
    
    # Sync to Redis (fast cache)
    try:
        update_task(task_id, {
            "status": "completed",
            "metadata": metadata
        })
        logger.debug(f"[{task_id[:8]}] ✓ Redis synchronized with metadata.json")
    except Exception as e:
        logger.warning(f"[{task_id[:8]}] Failed to sync Redis (non-critical): {e}")

    # Отправляем webhook если указан
    if webhook_url:
        webhook_payload = {
            "task_id": task_id,
            "event": "task_completed",
            "status": "completed",
            "input": metadata.get("input", {}),
            "output": metadata.get("output", {}),
            "completed_at": metadata["completed_at"]
        }
        # Добавляем webhook объект если есть
        if webhook_url or webhook_headers:
            webhook_obj = {}
            if webhook_url:
                webhook_obj["url"] = webhook_url
            if webhook_headers:
                webhook_obj["headers"] = webhook_headers
            webhook_payload["webhook"] = webhook_obj
        if client_meta is not None:
            webhook_payload["client_meta"] = client_meta
        send_webhook(webhook_url, webhook_payload, webhook_headers, task_id)

    # Return the same metadata that was saved to metadata.json
    # This ensures sync response = /task_status response = metadata.json content
    return jsonify(metadata)


def process_video_pipeline_background(task_id: str, video_url: str, operations: list, webhook: dict = None):
    """Фоновое выполнение pipeline операций с использованием task-based архитектуры"""

    # Извлекаем webhook_url, webhook_headers и client_meta из webhook объекта
    webhook_url = None
    webhook_headers = None
    client_meta = None
    if webhook:
        webhook_url = webhook.get('url')
        webhook_headers = webhook.get('headers')
        client_meta = webhook.get('client_meta')

    try:
        # Создаем директории для задачи
        create_task_dirs(task_id)
        
        update_task(task_id, {'status': 'processing', 'progress': 5})

        # Скачиваем исходное видео
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(get_task_dir(task_id), f"input_{input_filename}")

        logger.info(f"Task {task_id}: Downloading video from {video_url}")
        ok, msg = download_media_with_validation(video_url, input_path)
        if not ok:
            raise Exception(msg)

        update_task(task_id, {'progress': 20})

        current_input = input_path
        final_outputs = []  # Может быть несколько выходных файлов (например при chunking)

        # Выполняем операции последовательно
        total_ops = len(operations)
        for idx, op_data in enumerate(operations):
            op_type = op_data['type']
            operation = OPERATIONS_REGISTRY[op_type]

            # Прогресс: 20% + (idx / total_ops) * 70%
            progress = 20 + int((idx / total_ops) * 70)
            update_task(task_id, {'progress': progress, 'current_operation': op_type})

            # Генерируем выходной файл
            if idx == total_ops - 1:
                # Последняя операция - финальный файл с семантическим префиксом
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                # Определяем префикс в зависимости от типа операции
                if op_type == 'make_short':
                    prefix = 'short'
                elif op_type == 'cut_video':
                    prefix = 'video'
                elif op_type == 'extract_audio':
                    prefix = 'audio'
                else:
                    prefix = 'processed'
                
                output_filename = f"{prefix}_{timestamp}.mp4"
                output_path = os.path.join(get_task_dir(task_id), output_filename)
            else:
                # Промежуточный файл
                output_path = os.path.join(get_task_dir(task_id), f"temp_{idx}_{uuid.uuid4()}.mp4")

            logger.info(f"Task {task_id}: Executing operation {idx+1}/{total_ops}: {op_type}")

            # Выполняем операцию
            result = operation.execute(current_input, output_path, op_data)
            
            # Обрабатываем результат (может быть 2 или 3 значения)
            if len(result) == 3:
                success, message, actual_output = result
                # Если операция вернула список файлов (например chunks)
                if isinstance(actual_output, list):
                    output_paths = actual_output
                # Если операция вернула другой путь (например extract_audio создал .mp3)
                elif actual_output and actual_output != output_path:
                    output_paths = [actual_output]
                else:
                    output_paths = [output_path]
            else:
                success, message = result
                output_paths = [output_path]

            if not success:
                raise Exception(f"Operation '{op_type}' failed: {message}")

            # Если это последняя операция - сохраняем все выходные файлы
            if idx == total_ops - 1:
                final_outputs = output_paths
            
            # Удаляем предыдущий временный файл
            if current_input != input_path and os.path.exists(current_input):
                os.remove(current_input)

            # Следующая операция будет использовать первый файл как вход
            current_input = output_paths[0] if output_paths else output_path

        # Удаляем исходный файл
        if os.path.exists(input_path):
            os.remove(input_path)

        # Финальный результат
        if not final_outputs:
            raise Exception("Final output file not found. This may happen if operations failed or no operations were executed.")

        # Устанавливаем права доступа для всех выходных файлов
        for output_file in final_outputs:
            if os.path.exists(output_file):
                os.chmod(output_file, 0o644)

        update_task(task_id, {'progress': 95})

        # Собираем информацию о выходных файлах
        output_files_info = []

        # Построение карты chunk-информации по шаблону имени *_chunkNNN.ext
        pattern = re.compile(r"^(?P<prefix>.+)_chunk(?P<index>\d{3})\.(?P<ext>[^.]+)$")
        chunk_groups = {}
        for p in final_outputs:
            fname = os.path.basename(p)
            m = pattern.match(fname)
            if m:
                prefix = m.group('prefix')
                idx = int(m.group('index'))
                chunk_groups.setdefault(prefix, []).append((fname, idx))
        chunk_map = {}
        for prefix, lst in chunk_groups.items():
            total = len(lst)
            for fname, idx in lst:
                chunk_map[fname] = {
                    'chunk': f"{idx + 1}:{total}"
                }

        total_size = 0
        for output_file in final_outputs:
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                total_size += file_size
                filename = os.path.basename(output_file)
                
                entry = {
                    'filename': filename,
                    'file_size': file_size,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'download_path': f"/download/{task_id}/{filename}",
                    'download_url_internal': build_internal_url_background(f"/download/{task_id}/{filename}")
                }
                # Добавляем download_url только если есть публичный URL (API_KEY + PUBLIC_BASE_URL)
                if API_KEY_ENABLED and PUBLIC_BASE_URL:
                    entry['download_url'] = build_absolute_url_background(f"/download/{task_id}/{filename}")
                if filename in chunk_map:
                    entry.update(chunk_map[filename])
                output_files_info.append(entry)

        # Сохраняем метаданные
        # Попробуем получить client_meta из сохраненной задачи
        task_snapshot = get_task(task_id) or {}
        client_meta = task_snapshot.get('client_meta')
        is_chunked = any(f.get('chunk') for f in output_files_info)
        
        # Вычисляем expires_at
        expires_at_iso = task_snapshot.get('expires_at', (datetime.now() + timedelta(hours=TASK_TTL_HOURS)).isoformat())
        
        # Добавляем expires_at к каждому файлу
        for file_entry in output_files_info:
            file_entry["expires_at"] = expires_at_iso

        # Build complete metadata with input/output structure
        metadata = build_structured_metadata(
            task_id=task_id,
            status='completed',
            created_at=task_snapshot.get('created_at', datetime.now().isoformat()),
            completed_at=datetime.now().isoformat(),
            expires_at=expires_at_iso,
            video_url=video_url,
            operations=operations,
            output_files=output_files_info,
            total_files=len(output_files_info),
            is_chunked=is_chunked,
            metadata_url=build_absolute_url_background(f"/download/{task_id}/metadata.json") if (PUBLIC_BASE_URL and API_KEY) else None,
            metadata_url_internal=build_internal_url_background(f"/download/{task_id}/metadata.json"),
            webhook_url=webhook_url,
            webhook_headers=webhook_headers,
            webhook_status=None,
            retry_count=task_snapshot.get('retry_count', 0),
            client_meta=client_meta,
            operations_count=total_ops,
            total_size=total_size,
            total_size_mb=round(total_size / (1024 * 1024), 2),
            ttl_seconds=TASK_TTL_HOURS * 3600,
            ttl_human=format_ttl_human(TASK_TTL_HOURS)
        )
        
        # CRITICAL: Save metadata.json first (source of truth) with verification
        logger.info(f"[{task_id[:8]}] Saving final metadata.json (status=completed)")
        logger.debug(f"[{task_id[:8]}] Final metadata keys: {list(metadata.keys())}")
        try:
            write_ok = save_task_metadata(task_id, metadata, verify=True)
            if write_ok:
                logger.info(f"[{task_id[:8]}] ✓ Final metadata.json saved and verified successfully")
            else:
                logger.error(f"[{task_id[:8]}] ✗ CRITICAL: Failed to save final metadata")
        except Exception as e:
            logger.error(f"[{task_id[:8]}] ✗ CRITICAL: Failed to save final metadata: {e}")
            raise
        
        # Синхронизируем Redis с metadata.json для быстрого доступа (cache)
        # Храним полную структуру под ключом 'metadata' для моментального ответа
        try:
            update_task(task_id, {
                "status": "completed",
                "metadata": metadata  # Полная структура для моментального ответа
            })
            logger.debug(f"[{task_id[:8]}] ✓ Redis synchronized with metadata.json")
        except Exception as e:
            logger.warning(f"[{task_id[:8]}] Failed to sync Redis (non-critical): {e}")
            # Не критично - metadata.json уже сохранён

        logger.info(f"Task {task_id}: Completed successfully with {len(output_files_info)} output file(s)")

        # Отправляем финальный webhook если указан
        if webhook_url:
            # Читаем metadata для получения input/output
            final_metadata = load_task_metadata(task_id)
            webhook_payload = {
                'task_id': task_id,
                'event': 'task_completed',
                'status': 'completed',
                'input': final_metadata.get('input', {}),
                'output': final_metadata.get('output', {}),
                'completed_at': datetime.now().isoformat()
            }
            # Добавляем webhook объект если есть
            if webhook_url or webhook_headers:
                webhook_obj = {}
                if webhook_url:
                    webhook_obj["url"] = webhook_url
                if webhook_headers:
                    webhook_obj["headers"] = webhook_headers
                webhook_payload["webhook"] = webhook_obj
            # client_meta в самом конце
            if client_meta is not None:
                webhook_payload['client_meta'] = client_meta
            send_webhook(webhook_url, webhook_payload, webhook_headers, task_id)

    except Exception as e:
        logger.error(f"Task {task_id}: Error - {e}")
        
        # Get task snapshot from Redis or use defaults
        task_snapshot = get_task(task_id) or {}
        
        # Create full error metadata structure
        now = datetime.now()
        error_metadata = build_structured_metadata(
            task_id=task_id,
            status="error",
            created_at=task_snapshot.get('created_at', now.isoformat()),
            completed_at=now.isoformat(),
            expires_at=(now + timedelta(hours=TASK_TTL_HOURS)).isoformat(),
            video_url=video_url,
            operations=operations,
            output_files=[],
            total_files=0,
            is_chunked=False,
            metadata_url=None,
            metadata_url_internal=None,
            webhook_url=webhook_url,
            webhook_headers=webhook_headers,
            webhook_status=None,
            retry_count=task_snapshot.get('retry_count', 0),
            client_meta=client_meta,
            operations_count=len(operations),
            total_size=0,
            total_size_mb=0.0,
            ttl_seconds=TASK_TTL_HOURS * 3600,
            ttl_human=format_ttl_human(TASK_TTL_HOURS)
        )
        error_metadata["error"] = str(e)
        error_metadata["failed_at"] = now.isoformat()
        
        # Save error metadata
        save_task_metadata(task_id, error_metadata)
        
        # Sync to Redis
        try:
            update_task(task_id, {
                'status': 'error',
                'metadata': error_metadata
            })
        except Exception as sync_err:
            logger.warning(f"[{task_id[:8]}] Failed to sync error to Redis: {sync_err}")

        # Отправляем error webhook если указан
        if webhook_url:
            error_payload = {
                'task_id': task_id,
                'event': 'task_failed',
                'status': 'error',
                'input': error_metadata.get('input', {}),
                'error': str(e),
                'failed_at': error_metadata['failed_at']
            }
            # Добавляем webhook объект если есть
            if webhook_url or webhook_headers:
                webhook_obj = {}
                if webhook_url:
                    webhook_obj["url"] = webhook_url
                if webhook_headers:
                    webhook_obj["headers"] = webhook_headers
                error_payload["webhook"] = webhook_obj
            if client_meta is not None:
                error_payload['client_meta'] = client_meta
            send_webhook(webhook_url, error_payload, webhook_headers, task_id)


def recover_stuck_tasks():
    """Сканирует задачи и перезапускает зависшие (recovery механизм)"""
    if not RECOVERY_ENABLED:
        logger.info("Recovery disabled (RECOVERY_ENABLED=false)")
        return
    
    logger.info("=" * 60)
    logger.info("Starting task recovery scan...")
    current_time = datetime.now()
    recovered = 0
    failed = 0
    expired = 0
    scanned = 0
    skipped_status = 0
    skipped_with_output = 0
    skipped_webhook_failed = 0
    empty_dirs_removed = 0
    
    try:
        for task_id in os.listdir(TASKS_DIR):
            scanned += 1
            task_dir = get_task_dir(task_id)
            metadata_path = os.path.join(task_dir, "metadata.json")

            if not os.path.exists(metadata_path):
                # Пустая директория без метаданных - удаляем
                try:
                    if os.path.isdir(task_dir):
                        import shutil
                        shutil.rmtree(task_dir, ignore_errors=True)
                        logger.info(f"Removed empty task directory: {task_id}")
                        empty_dirs_removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove empty dir {task_id}: {e}")
                continue

            try:
                metadata = load_task_metadata(task_id)
                if not metadata:
                    continue

                status = metadata.get('status')

                # Если задача завершена, но вебхук не доставлен — считаем отдельно
                if status == 'completed':
                    webhook = metadata.get('webhook')
                    # webhook может быть dict или None
                    if webhook and webhook.get('status') != 'delivered':
                        skipped_webhook_failed += 1
                        logger.debug(f"Task {task_id}: Completed but webhook not delivered (webhook_status={webhook.get('status')})")
                    skipped_status += 1
                    logger.debug(f"Task {task_id}: Skip (status={status})")
                    continue

                # Диагностика: считаем пропущенные по статусу
                # В recovery теперь включаем 'pending' (задачи могли упасть до смены статуса)
                if status not in ('processing', 'queued', 'pending'):
                    skipped_status += 1
                    logger.debug(f"Task {task_id}: Skip (status={status})")
                    continue
                
                # Проверяем истек ли TTL
                expires_at_str = metadata.get('expires_at')
                if not expires_at_str:
                    # Старая задача без expires_at - добавляем на основе created_at
                    created_at = datetime.fromisoformat(metadata.get('created_at', current_time.isoformat()))
                    expires_at = created_at + timedelta(hours=TASK_TTL_HOURS)
                else:
                    expires_at = datetime.fromisoformat(expires_at_str)
                
                # Если задача истекла → failed
                if current_time > expires_at:
                    metadata['status'] = 'failed'
                    metadata['error'] = f'Task expired (TTL {TASK_TTL_HOURS}h exceeded)'
                    metadata['failed_at'] = current_time.isoformat()
                    save_task_metadata(task_id, metadata)
                    update_task(task_id, {
                        'status': 'failed',
                        'error': metadata['error'],
                        'failed_at': metadata['failed_at']
                    })
                    logger.warning(f"Task {task_id}: Expired (TTL exceeded)")
                    expired += 1
                    continue
                
                # Проверяем есть ли уже output файлы (префиксы: short_, video_, audio_)
                files = os.listdir(task_dir)
                has_output = any(f.startswith(('short_', 'video_', 'audio_')) for f in files)
                
                if has_output:
                    # Результат есть, но статус не обновлен
                    skipped_with_output += 1
                    logger.info(f"Task {task_id}: Has output but status={status}, skipping recovery")
                    continue
                
                # Проверяем количество попыток
                retry_count = metadata.get('retry_count', 0)
                
                if retry_count >= MAX_TASK_RETRIES:
                    # Слишком много попыток
                    metadata['status'] = 'failed'
                    metadata['error'] = f'Max retries exceeded ({retry_count}/{MAX_TASK_RETRIES})'
                    metadata['failed_at'] = current_time.isoformat()
                    save_task_metadata(task_id, metadata)
                    update_task(task_id, {
                        'status': 'failed',
                        'error': metadata['error'],
                        'failed_at': metadata['failed_at']
                    })
                    logger.warning(f"Task {task_id}: Max retries exceeded ({retry_count})")
                    failed += 1
                    continue
                
                # Удаляем временные файлы перед retry
                for filename in files:
                    if filename.startswith('temp_'):
                        try:
                            os.remove(os.path.join(task_dir, filename))
                            logger.info(f"Task {task_id}: Deleted temp file: {filename}")
                        except Exception as e:
                            logger.warning(f"Task {task_id}: Failed to delete {filename}: {e}")
                
                # Проверяем есть ли входной файл и валиден ли он
                has_valid_input = False
                input_file = None
                for filename in files:
                    if filename.startswith('input_'):
                        input_path = os.path.join(task_dir, filename)
                        if os.path.exists(input_path) and os.path.getsize(input_path) > 1024:  # > 1KB
                            has_valid_input = True
                            input_file = input_path
                            logger.info(f"Task {task_id}: Found valid input file: {filename}")
                            break
                
                # Перезапускаем задачу
                logger.info(f"Task {task_id}: Recovering (retry {retry_count + 1}/{MAX_TASK_RETRIES})")
                metadata['retry_count'] = retry_count + 1
                metadata['last_retry_at'] = current_time.isoformat()
                metadata['status'] = 'processing'
                save_task_metadata(task_id, metadata)
                
                # Обновляем статус в хранилище
                update_task(task_id, {
                    'status': 'processing',
                    'retry_count': retry_count + 1,
                    'last_retry_at': metadata['last_retry_at']
                })
                
                # Запускаем обработку в фоне
                # Если входной файл есть и валиден - не перезагружаем
                # Иначе process_video_pipeline_background сам загрузит
                video_url = metadata.get('input', {}).get('video_url')
                operations = metadata.get('input', {}).get('operations', [])
                webhook = metadata.get('webhook')

                if not has_valid_input:
                    logger.info(f"Task {task_id}: No valid input file, will re-download")

                thread = threading.Thread(
                    target=process_video_pipeline_background,
                    args=(task_id, video_url, operations, webhook),
                    daemon=True
                )
                thread.start()
                
                recovered += 1
                
                # Добавляем задержку между попытками
                if RETRY_DELAY_SECONDS > 0:
                    import time
                    time.sleep(RETRY_DELAY_SECONDS)
                
            except Exception as e:
                logger.error(f"Task {task_id}: Recovery error - {e}")
                failed += 1
                
    except Exception as e:
        logger.error(f"Recovery scan error: {e}")
    
    logger.info(
        "Recovery scan complete: "
        f"scanned={scanned}, recovered={recovered}, expired={expired}, failed={failed}, "
        f"skipped_status={skipped_status}, skipped_with_output={skipped_with_output}, "
        f"skipped_webhook_failed={skipped_webhook_failed}, empty_dirs_removed={empty_dirs_removed}"
    )
    logger.info("=" * 60)

def schedule_recovery():
    """Запускает recovery периодически если RECOVERY_INTERVAL_MINUTES > 0"""
    if RECOVERY_INTERVAL_MINUTES > 0:
        import time
        logger.info(f"Recovery scheduler started (interval: {RECOVERY_INTERVAL_MINUTES} min)")
        while True:
            time.sleep(RECOVERY_INTERVAL_MINUTES * 60)
            recover_stuck_tasks()


# ============================================
# РУЧНОЕ ВОССТАНОВЛЕНИЕ ПО task_id (публично, если включено)
# ============================================

def _recover_task_by_id(task_id: str, force: bool = False) -> tuple[bool, str, dict]:
    """Пытается восстановить конкретную задачу по task_id.
    Возвращает (ok, message, extra_info).
    """
    task_dir = get_task_dir(task_id)
    if not os.path.isdir(task_dir):
        return False, "Task directory not found", {}

    metadata = load_task_metadata(task_id)
    if not metadata:
        return False, "metadata.json not found", {}

    status = metadata.get('status')
    if status == 'completed':
        return True, "Task already completed", {"status": status}

    # TTL check
    try:
        current_time = datetime.now()
        expires_at = metadata.get('expires_at')
        if expires_at:
            exp_dt = datetime.fromisoformat(expires_at)
            if current_time > exp_dt and not force:
                return False, "Task expired (TTL exceeded). Use force=1 to override.", {"status": status}
    except Exception:
        pass

    # Cleanup temp_ files
    files = []
    try:
        files = os.listdir(task_dir)
    except Exception:
        files = []
    for filename in files:
        if filename.startswith('temp_'):
            try:
                os.remove(os.path.join(task_dir, filename))
            except Exception:
                pass

    # Prepare retry counters
    retry_count = int(metadata.get('retry_count', 0)) + 1
    metadata['retry_count'] = retry_count
    metadata['last_retry_at'] = datetime.now().isoformat()
    metadata['status'] = 'processing'
    save_task_metadata(task_id, metadata)

    # Also reflect in task storage if present
    update_task(task_id, {
        'status': 'processing',
        'retry_count': retry_count,
        'last_retry_at': metadata['last_retry_at']
    })

    video_url = metadata.get('input', {}).get('video_url')
    operations = metadata.get('input', {}).get('operations', [])
    webhook = metadata.get('webhook')
    if not video_url or not operations:
        return False, "Missing video_url or operations in metadata['input']", {}

    # Fire background processing
    thread = threading.Thread(
        target=process_video_pipeline_background,
        args=(task_id, video_url, operations, webhook),
        daemon=True
    )
    thread.start()
    return True, "Recovery started", {"status": 'processing', "retry_count": retry_count}


@app.route('/recover/<task_id>', methods=['GET', 'POST'])
def recover_task_endpoint(task_id):
    """Ручное восстановление конкретной задачи по task_id.
    По умолчанию доступ запрещён; включите RECOVERY_PUBLIC_ENABLED=true для публичного доступа без API-ключа.
    Поддерживает параметр query: force=1 (игнорировать TTL-истечение).
    """
    try:
        if not RECOVERY_PUBLIC_ENABLED and API_KEY_ENABLED:
            # В публичном режиме без явного разрешения — блокируем
            return jsonify({
                'status': 'error',
                'error': 'Public recovery endpoint is disabled'
            }), 403

        force = str(request.args.get('force', '0')).lower() in ('1', 'true', 'yes')
        ok, msg, info = _recover_task_by_id(task_id, force=force)
        code = 200 if ok else 400
        resp = {
            'task_id': task_id,
            'ok': ok,
            'message': msg,
        }
        resp.update(info)
        return jsonify(resp), code
    except Exception as e:
        logger.error(f"Manual recover error for {task_id}: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500


# ==============================================================================
# BACKGROUND WEBHOOK RESENDER
# ==============================================================================

def _webhook_resender_loop():
    """
    Фоновый процесс для автоматических ретраев webhook.
    Сканирует все задачи и отправляет webhooks для failed/pending статусов.
    """
    import time
    logger.info(f"Webhook resender started (interval: {WEBHOOK_BACKGROUND_INTERVAL_SECONDS}s)")

    while True:
        try:
            time.sleep(WEBHOOK_BACKGROUND_INTERVAL_SECONDS)

            logger.debug("Webhook resender: scanning tasks...")

            if not os.path.exists(TASKS_DIR):
                continue

            scanned = 0
            retried = 0


            for task_id in os.listdir(TASKS_DIR):
                task_path = os.path.join(TASKS_DIR, task_id)
                if not os.path.isdir(task_path):
                    continue

                scanned += 1

                # Загружаем metadata
                metadata = load_task_metadata(task_id)
                if not metadata:
                    continue

                # Пропускаем активные задачи
                status = metadata.get('status')
                if status in ['queued', 'processing']:
                    continue

                # Используем только metadata.json['webhook'] для состояния вебхука
                webhook_state = metadata.get('webhook')
                if not webhook_state:
                    logger.debug(f"[{task_id[:8]}] No webhook state found in metadata.json")
                    continue
                logger.debug(f"[{task_id[:8]}] Using webhook state from metadata.json['webhook']")

                # Пропускаем если уже доставлен
                if webhook_state.get('status') == 'delivered':
                    continue

                # URL вебхука: из state или из DEFAULT_WEBHOOK_URL
                webhook_url = webhook_state.get('url') or DEFAULT_WEBHOOK_URL
                if not webhook_url:
                    continue

                # Проверяем next_retry время
                next_retry = webhook_state.get('next_retry')
                if next_retry:
                    try:
                        next_retry_dt = datetime.fromisoformat(next_retry)
                        if datetime.now() < next_retry_dt:
                            logger.debug(f"[{task_id[:8]}] Skipping (next_retry: {next_retry})")
                            continue
                    except Exception:
                        pass

                # Формируем webhook payload
                webhook_headers = webhook_state.get('headers')

                if status == 'completed':
                    # Success webhook (строго: input/output из metadata)
                    webhook_payload = {
                        "task_id": task_id,
                        "event": "task_completed",
                        "status": "completed",
                        "input": metadata.get('input', {}),
                        "output": metadata.get('output', {}),
                        "completed_at": metadata.get('completed_at')
                    }
                    # Добавляем webhook объект если есть
                    if webhook_url or webhook_headers:
                        webhook_obj = {}
                        if webhook_url:
                            webhook_obj["url"] = webhook_url
                        if webhook_headers:
                            webhook_obj["headers"] = webhook_headers
                        webhook_payload["webhook"] = webhook_obj
                    client_meta = metadata.get('client_meta')
                    if client_meta:
                        webhook_payload['client_meta'] = client_meta

                elif status == 'error':
                    # Error webhook
                    webhook_payload = {
                        "task_id": task_id,
                        "event": "task_failed",
                        "status": "error",
                        "error": metadata.get('error', 'Unknown error'),
                        "failed_at": metadata.get('failed_at')
                    }

                    # Добавляем webhook объект если есть
                    if webhook_url or webhook_headers:
                        webhook_obj = {}
                        if webhook_url:
                            webhook_obj["url"] = webhook_url
                        if webhook_headers:
                            webhook_obj["headers"] = webhook_headers
                        webhook_payload["webhook"] = webhook_obj

                    client_meta = metadata.get('client_meta')
                    if client_meta:
                        webhook_payload['client_meta'] = client_meta
                else:
                    # Неизвестный статус
                    continue

                # Отправляем webhook
                logger.info(f"[{task_id[:8]}] Resender: retrying webhook (status={status})")
                _post_webhook(webhook_url, webhook_payload, webhook_headers, task_id, max_retries=3)
                retried += 1

            if retried > 0:
                logger.info(f"Webhook resender: scanned {scanned} tasks, retried {retried} webhooks")

        except Exception as e:
            logger.error(f"Webhook resender error: {e}")



# Запускаем resender только в первом gunicorn worker (аналогично youtube-downloader-api)

# Запускаем resender только в первом gunicorn worker (аналогично youtube-downloader-api)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)

# Запускаем resender только в первом gunicorn worker (аналогично youtube-downloader-api)
marker_file = '/tmp/vpapi_resender_started'
try:
    if not os.path.exists(marker_file):
        with open(marker_file, 'w') as f:
            f.write(str(os.getpid()))
        _resender_thread = threading.Thread(target=_webhook_resender_loop, name='webhook-resender', daemon=True)
        _resender_thread.start()
        logger.debug(f"Resender thread started in process {os.getpid()}")
except Exception as e:
    logger.warning(f"Failed to start resender thread: {e}")
