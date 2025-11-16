from flask import Flask, request, jsonify, send_file
import os
import subprocess
from datetime import datetime, timedelta
import uuid
import logging
import threading
from typing import Dict, Any
import re
import json
from functools import wraps

app = Flask(__name__)

# Отключаем автоматическую сортировку ключей JSON (сохраняем порядок вставки)
# Flask 3.0+ требует явного указания в json provider
app.json.sort_keys = False

# ============================================
# API KEY AUTHENTICATION
# ============================================

PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL') or os.getenv('EXTERNAL_BASE_URL')
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
    internal_base = os.getenv('INTERNAL_BASE_URL', 'http://video-processor:5001')
    return _join_url(internal_base, path)

# ============================================
# TASK STORAGE - Redis (multi-worker) or In-Memory (single-worker)
# ============================================

# Try to connect to Redis if available
redis_client = None
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

try:
    import redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    redis_client.ping()
    STORAGE_MODE = "redis"
except Exception as e:
    redis_client = None
    STORAGE_MODE = "memory"

# Fallback: In-memory storage (only for single worker!)
tasks_memory: Dict[str, Dict[str, Any]] = {}

def save_task(task_id: str, task_data: dict):
    """Save task to Redis or memory"""
    if STORAGE_MODE == "redis":
        redis_client.setex(
            f"task:{task_id}",
            86400,  # 24 hours TTL
            json.dumps(task_data)
        )
    else:
        tasks_memory[task_id] = task_data

def get_task(task_id: str) -> dict:
    """Get task from Redis or memory"""
    if STORAGE_MODE == "redis":
        data = redis_client.get(f"task:{task_id}")
        return json.loads(data) if data else None
    else:
        return tasks_memory.get(task_id)

def update_task(task_id: str, updates: dict):
    """Update task in Redis or memory"""
    task = get_task(task_id)
    if task:
        task.update(updates)
        save_task(task_id, task)

def list_tasks() -> list:
    """List all tasks from Redis or memory"""
    if STORAGE_MODE == "redis":
        keys = redis_client.keys("task:*")
        tasks = []
        for key in keys[-100:]:  # Last 100 tasks
            data = redis_client.get(key)
            if data:
                tasks.append(json.loads(data))
        return tasks
    else:
        return list(tasks_memory.values())[-100:]

# Конфигурация
TASKS_DIR = "/app/tasks"
os.makedirs(TASKS_DIR, exist_ok=True)

# Recovery настройки
RECOVERY_ENABLED = os.getenv('RECOVERY_ENABLED', 'true').lower() in ('true', '1', 'yes')
RECOVERY_INTERVAL_MINUTES = int(os.getenv('RECOVERY_INTERVAL_MINUTES', '0'))  # 0 = только при старте
MAX_TASK_RETRIES = int(os.getenv('MAX_TASK_RETRIES', '3'))
RETRY_DELAY_SECONDS = int(os.getenv('RETRY_DELAY_SECONDS', '60'))
TASK_TTL_HOURS = int(os.getenv('TASK_TTL_HOURS', '2'))  # Время жизни задачи

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

def save_task_metadata(task_id: str, metadata: dict):
    """Сохранить metadata.json для задачи"""
    metadata_path = os.path.join(get_task_dir(task_id), "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    os.chmod(metadata_path, 0o644)

def load_task_metadata(task_id: str) -> dict:
    """Загрузить metadata.json для задачи"""
    metadata_path = os.path.join(get_task_dir(task_id), "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return None

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_startup_info():
    """Выводит информацию о конфигурации сервиса при старте."""
    logger.info("=" * 60)
    logger.info("Video Processor API starting...")
    logger.info(f"Storage mode: {STORAGE_MODE}")
    if STORAGE_MODE == "redis":
        logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT} (db={REDIS_DB})")
        logger.info("Multi-worker support: ENABLED")
    else:
        logger.info("Redis: Not available")
        logger.info("Multi-worker support: DISABLED (use --workers 1)")

    # Log API access mode
    if API_KEY_ENABLED:
        # Публичный режим (API_KEY задан)
        if PUBLIC_BASE_URL:
            logger.info("Mode: PUBLIC API with external URLs")
            logger.info(f"Base URL: {PUBLIC_BASE_URL}")
            logger.info("Authentication: ENABLED (Bearer token required)")
        else:
            logger.info("Mode: PUBLIC API with internal URLs")
            logger.info("Authentication: ENABLED (Bearer token required)")
    else:
        # Внутренний режим (API_KEY не задан)
        logger.info("Mode: INTERNAL (Docker network)")
        if PUBLIC_BASE_URL:
            logger.warning("=" * 60)
            logger.warning("WARNING: PUBLIC_BASE_URL is set but API_KEY is not!")
            logger.warning(f"PUBLIC_BASE_URL will be IGNORED: {PUBLIC_BASE_URL}")
            logger.warning("To activate public mode with external URLs:")
            logger.warning("  1. Generate API key: openssl rand -hex 32")
            logger.warning("  2. Set API_KEY environment variable")
            logger.warning("=" * 60)
        logger.info("Authentication: DISABLED (internal network)")

    # Отобразим число воркеров если задано
    try:
        workers_env = os.getenv('WORKERS')
        if workers_env:
            logger.info(f"Workers (gunicorn): {workers_env}")
    except Exception:
        pass
    
    # Recovery настройки
    if RECOVERY_ENABLED:
        logger.info(f"Recovery: ENABLED")
        logger.info(f"  - Task TTL: {TASK_TTL_HOURS}h")
        logger.info(f"  - Max retries: {MAX_TASK_RETRIES}")
        logger.info(f"  - Retry delay: {RETRY_DELAY_SECONDS}s")
        if RECOVERY_INTERVAL_MINUTES > 0:
            logger.info(f"  - Interval: {RECOVERY_INTERVAL_MINUTES} min (periodic)")
        else:
            logger.info(f"  - Interval: startup only")
    else:
        logger.info("Recovery: DISABLED")

    logger.info("=" * 60)

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

# Ограничения для client_meta, чтобы избежать перегрузки сервиса и инъекций
MAX_CLIENT_META_BYTES = int(os.getenv('MAX_CLIENT_META_BYTES', 16 * 1024))  # 16 KB по умолчанию
MAX_CLIENT_META_DEPTH = int(os.getenv('MAX_CLIENT_META_DEPTH', 5))
MAX_CLIENT_META_KEYS = int(os.getenv('MAX_CLIENT_META_KEYS', 200))
MAX_CLIENT_META_STRING_LENGTH = int(os.getenv('MAX_CLIENT_META_STRING_LENGTH', 1000))
MAX_CLIENT_META_LIST_LENGTH = int(os.getenv('MAX_CLIENT_META_LIST_LENGTH', 200))

ALLOWED_JSON_PRIMITIVES = (str, int, float, bool, type(None))

# Разрешить ли попытку распарсить вложенные JSON-строки в client_meta
ALLOW_NESTED_JSON_IN_META = os.getenv('ALLOW_NESTED_JSON_IN_META', 'true').lower() in ('1', 'true', 'yes')


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

# Вызов логирования после определения всех констант — выводим один раз на контейнер
_log_startup_once()

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
    """Удаляет задачи старше 2 часов"""
    import time
    import shutil
    current_time = time.time()
    try:
        if not os.path.exists(TASKS_DIR):
            return
        
        for task_id in os.listdir(TASKS_DIR):
            task_path = os.path.join(TASKS_DIR, task_id)
            if not os.path.isdir(task_path):
                continue
            
            # Проверяем время создания директории задачи
            if current_time - os.path.getctime(task_path) > 7200:  # 2 часа
                shutil.rmtree(task_path, ignore_errors=True)
                logger.info(f"Cleaned up old task: {task_id}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


def send_webhook(webhook_url: str, payload: dict, max_retries: int = 3) -> bool:
    """
    Отправляет webhook с retry логикой

    Args:
        webhook_url: URL для отправки webhook
        payload: Данные для отправки (JSON)
        max_retries: Максимальное количество попыток (default: 3)

    Returns:
        True если успешно отправлено, False если все попытки провалились
    """
    import requests
    import time

    if not webhook_url:
        return False

    for attempt in range(max_retries):
        try:
            logger.info(f"Sending webhook to {webhook_url} (attempt {attempt + 1}/{max_retries})")

            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )

            response.raise_for_status()
            logger.info(f"Webhook sent successfully to {webhook_url}")
            return True

        except requests.exceptions.RequestException as e:
            logger.warning(f"Webhook attempt {attempt + 1}/{max_retries} failed: {e}")

            if attempt < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                sleep_time = 2 ** attempt
                logger.info(f"Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"All {max_retries} webhook attempts failed for {webhook_url}")
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
                'subtitles': {}
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

        return True, "Converted to Shorts format (1080x1920)"


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


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (не требует авторизации)"""
    return jsonify({
        "status": "healthy",
        "service": "video-processor-api",
        "storage_mode": STORAGE_MODE,
        "redis_available": STORAGE_MODE == "redis",
        "api_key_enabled": API_KEY_ENABLED,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/fonts', methods=['GET'])
@require_api_key
def list_fonts():
    """
    Получить список доступных шрифтов
    Возвращает системные шрифты + кастомные шрифты из /app/fonts/custom
    """
    try:
        fonts = {
            "system_fonts": [],
            "custom_fonts": []
        }

        # Системные шрифты (встроенные в контейнер)
        system_fonts_list = [
            {"name": "DejaVu Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"},
            {"name": "DejaVu Sans Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"},
            {"name": "DejaVu Serif", "family": "serif", "file": "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"},
            {"name": "Liberation Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"},
            {"name": "Liberation Sans Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"},
            {"name": "Liberation Serif", "family": "serif", "file": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"},
            {"name": "Liberation Mono", "family": "monospace", "file": "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"},
            {"name": "Noto Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"},
            {"name": "Roboto", "family": "sans-serif", "file": "/usr/share/fonts/truetype/roboto/Roboto-Regular.ttf"},
            {"name": "Roboto Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf"},
            {"name": "Open Sans", "family": "sans-serif", "file": "/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf"},
            {"name": "Open Sans Bold", "family": "sans-serif", "file": "/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf"}
        ]

        # Проверяем какие системные шрифты реально существуют
        for font in system_fonts_list:
            if os.path.exists(font["file"]):
                fonts["system_fonts"].append(font)

        # Кастомные шрифты из /app/fonts/custom
        custom_fonts_dir = "/app/fonts/custom"
        if os.path.exists(custom_fonts_dir):
            for filename in os.listdir(custom_fonts_dir):
                if filename.lower().endswith(('.ttf', '.otf')):
                    font_path = os.path.join(custom_fonts_dir, filename)
                    font_name = os.path.splitext(filename)[0].replace('-', ' ').replace('_', ' ')
                    fonts["custom_fonts"].append({
                        "name": font_name,
                        "family": "custom",
                        "file": font_path
                    })

        return jsonify({
            "status": "success",
            "total_fonts": len(fonts["system_fonts"]) + len(fonts["custom_fonts"]),
            "fonts": fonts
        })

    except Exception as e:
        logger.error(f"Error listing fonts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<path:file_path>', methods=['GET'])
def download_file(file_path):
    """Скачать файл из задачи (не требует авторизации - доступ по task_id)
    
    Поддерживаемые форматы:
    - /download/{task_id}/output/{filename}
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
    """Получить статус задачи (не требует авторизации - task_id уникален)"""
    try:
        task = get_task(task_id)

        # Fallback: если записи в хранилище нет — попробуем метаданные с диска
        if not task:
            metadata = load_task_metadata(task_id)
            if metadata and metadata.get('status') == 'completed':
                # Пересоберём абсолютные ссылки
                output_files = metadata.get('output_files', [])
                for f in output_files:
                    dp = f.get('download_path')
                    if dp:
                        f['download_url'] = build_absolute_url(dp)

                # Ответ в желаемом порядке, client_meta внизу
                resp = {
                    'task_id': task_id,
                    'status': 'completed',
                    'progress': 100,
                    'created_at': metadata.get('created_at'),
                    'video_url': metadata.get('video_url'),
                    'output_files': output_files,
                    'total_files': metadata.get('total_files', len(output_files)),
                    'total_size': metadata.get('total_size'),
                    'is_chunked': any(f.get('chunk') for f in output_files) if output_files else False,
                    'metadata_url': build_absolute_url(f"/download/{task_id}/metadata.json"),
                    'completed_at': metadata.get('completed_at')
                }
                if metadata.get('client_meta') is not None:
                    resp['client_meta'] = metadata.get('client_meta')
                return jsonify(resp)

            # Если директория задачи существует — считаем, что в процессе
            if os.path.isdir(get_task_dir(task_id)):
                resp = {
                    'task_id': task_id,
                    'status': 'processing',
                    'progress': 50
                }
                return jsonify(resp)

            return jsonify({"status": "error", "error": "Task not found"}), 404

        # Базовый ответ (без client_meta; добавим в конце)
        response = {
            'task_id': task_id,
            'status': task['status'],
            'progress': task.get('progress', 0),
            'created_at': task.get('created_at')
        }

        if task['status'] == 'completed':
            output_files = task.get('output_files', [])
            for f in output_files:
                dp = f.get('download_path')
                if dp:
                    f['download_url'] = build_absolute_url(dp)
            is_chunked = any(f.get('chunk') for f in output_files) if output_files else False
            response.update({
                'video_url': task.get('video_url'),
                'output_files': output_files,
                'total_files': task.get('total_files', len(output_files)),
                'total_size': task.get('total_size'),
                'is_chunked': is_chunked,
                'metadata_url': build_absolute_url(f"/download/{task_id}/metadata.json"),
                'completed_at': task.get('completed_at')
            })
        elif task['status'] == 'error':
            response.update({
                'error': task.get('error'),
                'failed_at': task.get('failed_at')
            })

        # Добавляем client_meta в самом конце
        if task.get('client_meta') is not None:
            response['client_meta'] = task.get('client_meta')

        return jsonify(response)

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
        webhook_url = data.get('webhook_url', os.getenv('WEBHOOK_URL'))
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
                'webhook_url': webhook_url,
                'client_meta': client_meta,
                'created_at': now.isoformat(),
                'expires_at': (now + timedelta(hours=TASK_TTL_HOURS)).isoformat(),
                'retry_count': 0,
                'last_retry_at': None
            }
            save_task(task_id, task_data)

            # Запускаем фоновую обработку
            thread = threading.Thread(
                target=process_video_pipeline_background,
                args=(task_id, video_url, operations, webhook_url)
            )
            thread.daemon = True
            thread.start()

            logger.info(f"Task {task_id}: Created with {len(operations)} operations")

            resp = {
                "task_id": task_id,
                "status": "processing",
                "message": "Task created and processing in background",
                "check_status_url": build_absolute_url(f"/task_status/{task_id}")
            }
            if client_meta is not None:
                resp["client_meta"] = client_meta
            return jsonify(resp), 202

        else:
            # Синхронный режим
            task_id = str(uuid.uuid4())
            
            # Создаем директории для задачи
            create_task_dirs(task_id)
            
            return process_video_pipeline_sync(task_id, video_url, operations, webhook_url, client_meta)

    except Exception as e:
        logger.error(f"Process video error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500


def process_video_pipeline_sync(task_id: str, video_url: str, operations: list, webhook_url: str = None, client_meta: dict | None = None) -> dict:
    """Синхронное выполнение pipeline операций"""

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

        logger.info(f"Task {task_id}: Executing operation {idx+1}/{len(operations)}: {op_type}")

        # Выполняем операцию
        result = operation.execute(current_input, output_path, op_data)
        
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
            return jsonify({"status": "error", "error": message, "task_id": task_id}), 500
        
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
            filename = os.path.basename(file_path)
            download_path = f"/download/{task_id}/{filename}"
            
            entry = {
                "filename": filename,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "download_path": download_path,
                "download_url": build_absolute_url(download_path)
            }
            if filename in chunk_map:
                entry.update(chunk_map[filename])
            files_info.append(entry)

    # Сохраняем metadata
    now = datetime.now()
    metadata = {
        "task_id": task_id,
        "status": "completed",
        "video_url": video_url,
        "operations": operations,
        "output_files": files_info,
        "total_files": len(files_info),
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(hours=TASK_TTL_HOURS)).isoformat(),
        "completed_at": now.isoformat(),
        "retry_count": 0
    }
    # client_meta в самом конце
    if client_meta is not None:
        metadata["client_meta"] = client_meta
    save_task_metadata(task_id, metadata)

    # Отправляем webhook если указан
    if webhook_url:
        # Определяем chunked по наличию поля 'chunk'
        is_chunked = any(f.get('chunk') for f in files_info)
        
        webhook_payload = {
            "task_id": task_id,
            "event": "task_completed",
            "status": "completed",
            "video_url": video_url,
            "output_files": files_info,
            "total_files": len(files_info),
            "is_chunked": is_chunked,
            "metadata_url": build_absolute_url_background(f"/download/{task_id}/metadata.json"),
            "completed_at": metadata["completed_at"]
        }
        if client_meta is not None:
            webhook_payload["client_meta"] = client_meta
        send_webhook(webhook_url, webhook_payload)

    # Определяем chunked
    is_chunked = any(f.get('chunk') for f in files_info)

    response_body = {
        "task_id": task_id,
        "status": "completed",
        "video_url": video_url,
        "output_files": files_info,
        "total_files": len(files_info),
        "is_chunked": is_chunked,
        "metadata_url": build_absolute_url(f"/download/{task_id}/metadata.json"),
        "note": "Files will auto-delete after 2 hours.",
        "completed_at": metadata["completed_at"]
    }
    # client_meta в самом конце
    if client_meta is not None:
        response_body["client_meta"] = client_meta
    return jsonify(response_body)


def process_video_pipeline_background(task_id: str, video_url: str, operations: list, webhook_url: str = None):
    """Фоновое выполнение pipeline операций с использованием task-based архитектуры"""

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
                # Последняя операция
                output_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}.mp4"
                output_path = os.path.join(get_task_dir(task_id), f"output_{output_filename}")
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
                    'download_url': build_absolute_url_background(f"/download/{task_id}/{filename}")
                }
                if filename in chunk_map:
                    entry.update(chunk_map[filename])
                output_files_info.append(entry)

        # Сохраняем метаданные
        # Попробуем получить client_meta из сохраненной задачи
        task_snapshot = get_task(task_id) or {}
        client_meta = task_snapshot.get('client_meta')

        metadata = {
            'task_id': task_id,
            'status': 'completed',
            'operations': operations,
            'operations_count': total_ops,
            'output_files': output_files_info,
            'total_files': len(output_files_info),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
                'created_at': task_snapshot.get('created_at', datetime.now().isoformat()),
                'expires_at': task_snapshot.get('expires_at', (datetime.now() + timedelta(hours=TASK_TTL_HOURS)).isoformat()),
                'completed_at': datetime.now().isoformat(),
                'retry_count': task_snapshot.get('retry_count', 0),
            'ttl_seconds': 7200,
            'ttl_human': '2 hours'
        }
        # client_meta в самом конце
        if client_meta is not None:
            metadata['client_meta'] = client_meta
        save_task_metadata(task_id, metadata)

        # Обновляем задачу
        update_task(task_id, {
            'status': 'completed',
            'progress': 100,
            'video_url': video_url,
            'output_files': output_files_info,
            'total_files': len(output_files_info),
            'total_size': total_size,
            'metadata_url': build_absolute_url_background(f"/download/{task_id}/metadata.json"),
            'operations_executed': total_ops,
            'completed_at': datetime.now().isoformat()
        })

        logger.info(f"Task {task_id}: Completed successfully with {len(output_files_info)} output file(s)")

        # Отправляем финальный webhook если указан
        if webhook_url:
            # Определяем chunked
            is_chunked = any(f.get('chunk') for f in output_files_info)
            
            webhook_payload = {
                'task_id': task_id,
                'event': 'task_completed',
                'status': 'completed',
                'video_url': video_url,
                'output_files': output_files_info,
                'total_files': len(output_files_info),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'is_chunked': is_chunked,
                'metadata_url': build_absolute_url_background(f"/download/{task_id}/metadata.json"),
                'file_ttl_seconds': 7200,
                'file_ttl_human': '2 hours',
                'operations_executed': total_ops,
                'completed_at': datetime.now().isoformat()
            }
            # client_meta в самом конце
            if client_meta is not None:
                webhook_payload['client_meta'] = client_meta
            send_webhook(webhook_url, webhook_payload)

    except Exception as e:
        logger.error(f"Task {task_id}: Error - {e}")
        update_task(task_id, {
            'status': 'error',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })

        # Отправляем error webhook если указан
        if webhook_url:
            error_payload = {
                'task_id': task_id,
                'event': 'task_failed',
                'status': 'error',
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            }
            send_webhook(webhook_url, error_payload)


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
    
    try:
        for task_id in os.listdir(TASKS_DIR):
            task_dir = get_task_dir(task_id)
            metadata_path = os.path.join(task_dir, "metadata.json")
            
            if not os.path.exists(metadata_path):
                # Пустая директория без метаданных - удаляем
                try:
                    if os.path.isdir(task_dir):
                        import shutil
                        shutil.rmtree(task_dir, ignore_errors=True)
                        logger.info(f"Removed empty task directory: {task_id}")
                except Exception as e:
                    logger.warning(f"Failed to remove empty dir {task_id}: {e}")
                continue
                
            try:
                metadata = load_task_metadata(task_id)
                if not metadata:
                    continue
                
                status = metadata.get('status')
                
                # Проверяем только processing задачи
                if status not in ('processing', 'queued'):
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
                    # Такое могло случиться если упали после обработки но до сохранения metadata
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
                video_url = metadata.get('video_url')
                operations = metadata.get('operations', [])
                webhook_url = metadata.get('webhook_url')
                
                if not has_valid_input:
                    logger.info(f"Task {task_id}: No valid input file, will re-download")
                
                thread = threading.Thread(
                    target=process_video_pipeline_background,
                    args=(task_id, video_url, operations, webhook_url),
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
    
    logger.info(f"Recovery scan complete: recovered={recovered}, expired={expired}, failed={failed}")
    logger.info("=" * 60)

def schedule_recovery():
    """Запускает recovery периодически если RECOVERY_INTERVAL_MINUTES > 0"""
    if RECOVERY_INTERVAL_MINUTES > 0:
        import time
        logger.info(f"Recovery scheduler started (interval: {RECOVERY_INTERVAL_MINUTES} min)")
        while True:
            time.sleep(RECOVERY_INTERVAL_MINUTES * 60)
            recover_stuck_tasks()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
