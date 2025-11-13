from flask import Flask, request, jsonify, send_file
import os
import subprocess
from datetime import datetime
import uuid
import logging
import threading
from typing import Dict, Any
import re
import json

app = Flask(__name__)

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

# Вспомогательные функции для работы с задачами
def get_task_dir(task_id: str) -> str:
    """Получить директорию задачи"""
    return os.path.join(TASKS_DIR, task_id)

def get_task_input_dir(task_id: str) -> str:
    """Получить директорию для входных файлов задачи"""
    return os.path.join(TASKS_DIR, task_id, "input")

def get_task_temp_dir(task_id: str) -> str:
    """Получить директорию для временных файлов задачи"""
    return os.path.join(TASKS_DIR, task_id, "temp")

def get_task_output_dir(task_id: str) -> str:
    """Получить директорию для выходных файлов задачи"""
    return os.path.join(TASKS_DIR, task_id, "output")

def create_task_dirs(task_id: str):
    """Создать структуру директорий для задачи"""
    os.makedirs(get_task_input_dir(task_id), exist_ok=True)
    os.makedirs(get_task_temp_dir(task_id), exist_ok=True)
    os.makedirs(get_task_output_dir(task_id), exist_ok=True)

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

# Log storage mode on startup
logger.info(f"=" * 60)
logger.info(f"Video Processor API starting...")
logger.info(f"Storage mode: {STORAGE_MODE}")
if STORAGE_MODE == "redis":
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT} (db={REDIS_DB})")
    logger.info(f"Multi-worker support: ENABLED")
else:
    logger.info(f"Redis: Not available")
    logger.info(f"Multi-worker support: DISABLED (use --workers 1)")
logger.info(f"=" * 60)

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
            
            # Проверяем время модификации папки output
            output_dir = get_task_output_dir(task_id)
            if os.path.exists(output_dir):
                if current_time - os.path.getmtime(output_dir) > 7200:  # 2 часа
                    shutil.rmtree(task_path)
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


class CutOperation(VideoOperation):
    """Операция нарезки видео"""
    def __init__(self):
        super().__init__(
            name="cut",
            required_params=["start_time", "end_time"],
            optional_params={}
        )

    def execute(self, input_path: str, output_path: str, params: dict, additional_inputs: dict = None) -> tuple[bool, str]:
        """Нарезка видео"""
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


class ToShortsOperation(VideoOperation):
    """Операция конвертации в Shorts формат"""
    def __init__(self):
        super().__init__(
            name="to_shorts",
            required_params=[],
            optional_params={
                'crop_mode': 'center',
                'letterbox_config': {},
                'title_text': '',
                'title_config': {},
                'subtitles': [],
                'subtitle_config': {}
            }
        )

    def execute(self, input_path: str, output_path: str, params: dict, additional_inputs: dict = None) -> tuple[bool, str]:
        """Конвертация в Shorts формат (1080x1920)"""
        # Применяем значения по умолчанию
        crop_mode = params.get('crop_mode', 'center')

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

        # Обработка title в новом формате (объект) или старом (разделенные поля)
        title_raw = params.get('title')
        if title_raw and isinstance(title_raw, dict):
            # Новый формат: {"text": "...", "font": "...", "fontsize": 70, ...}
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
        else:
            # Старый формат: title_text + title_config отдельно
            title_text = params.get('title_text', '')
            title_config_raw = params.get('title_config', {})
            title_config = {
                'fontfile': title_config_raw.get('fontfile'),
                'font': title_config_raw.get('font'),
                'fontsize': title_config_raw.get('fontsize', 70),
                'fontcolor': title_config_raw.get('fontcolor', 'white'),
                'bordercolor': title_config_raw.get('bordercolor', 'black'),
                'borderw': title_config_raw.get('borderw', 3),
                'text_align': title_config_raw.get('text_align', 'center'),
                'y': title_config_raw.get('y', 150),
                'start_time': title_config_raw.get('start_time', 0.5),
                'duration': title_config_raw.get('duration', 4),
                'fade_in': title_config_raw.get('fade_in', 0.5),
                'fade_out': title_config_raw.get('fade_out', 0.5)
            }

        # Обработка subtitles в новом формате (объект с items) или старом (прямой массив)
        subtitles_raw = params.get('subtitles')
        if subtitles_raw and isinstance(subtitles_raw, dict):
            # Новый формат: {"items": [...], "font": "...", "fontsize": 64, ...}
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
        else:
            # Старый формат: subtitles как массив + subtitle_config отдельно
            subtitles = params.get('subtitles', [])
            subtitle_config_raw = params.get('subtitle_config', {})
            subtitle_config = {
                'fontfile': subtitle_config_raw.get('fontfile'),
                'font': subtitle_config_raw.get('font'),
                'fontsize': subtitle_config_raw.get('fontsize', 60),
                'fontcolor': subtitle_config_raw.get('fontcolor', 'white'),
                'bordercolor': subtitle_config_raw.get('bordercolor', 'black'),
                'borderw': subtitle_config_raw.get('borderw', 3),
                'text_align': subtitle_config_raw.get('text_align', 'center'),
                'y': subtitle_config_raw.get('y', 'h-200')
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
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-filter_complex' if crop_mode == 'letterbox' else '-vf', video_filter,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]

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
    'cut': CutOperation(),
    'to_shorts': ToShortsOperation(),
    'extract_audio': ExtractAudioOperation(),
}


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "video-processor-api",
        "storage_mode": STORAGE_MODE,
        "redis_available": STORAGE_MODE == "redis",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/fonts', methods=['GET'])
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
    """Скачать файл из задачи
    
    Поддерживаемые форматы:
    - /download/{task_id}/output/{filename}
    - /download/{task_id}/metadata.json
    """
    try:
        full_path = os.path.join(TASKS_DIR, file_path)
        
        # Проверка безопасности - файл должен быть внутри TASKS_DIR
        if not os.path.abspath(full_path).startswith(os.path.abspath(TASKS_DIR)):
            return jsonify({"error": "Invalid file path"}), 403
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_file(full_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"error": str(e)}), 500

# ============================================
# АСИНХРОННАЯ ОБРАБОТКА
# ============================================

def process_video_background(task_id: str, video_url: str, start_time, end_time, crop_mode: str,
                           title_text: str = '', subtitles: list = None,
                           title_config: dict = None, subtitle_config: dict = None):
    """Фоновая обработка видео с использованием task-based архитектуры"""
    if title_config is None:
        title_config = {}
    if subtitle_config is None:
        subtitle_config = {}
    if subtitles is None:
        subtitles = []
    try:
        # Создаем директории для задачи
        create_task_dirs(task_id)
        
        update_task(task_id, {'status': 'processing', 'progress': 0})

        # Скачиваем видео в input директорию
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(get_task_input_dir(task_id), input_filename)

        logger.info(f"Task {task_id}: Downloading video from {video_url}")
        import requests
        response = requests.get(video_url, stream=True, timeout=300)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        update_task(task_id, {'progress': 30})

        # Создаём выходной файл в output директории
        output_filename = f"shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}.mp4"
        output_path = os.path.join(get_task_output_dir(task_id), output_filename)

        # Вычисляем длительность
        if isinstance(start_time, (int, float)) and isinstance(end_time, (int, float)):
            duration = end_time - start_time
            start_str = str(start_time)
            duration_str = str(duration)
        else:
            start_str = str(start_time)
            duration_str = None

        # Определяем фильтр обрезки
        if crop_mode == 'letterbox':
            # Letterbox: горизонтальное видео по центру + размытый фон
            video_filter = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];"
                "[0:v]scale=-1:1080:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2"
            )
        elif crop_mode == 'top':
            video_filter = "crop=ih*9/16:ih:0:0,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        elif crop_mode == 'bottom':
            video_filter = "crop=ih*9/16:ih:0:ih-oh,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        else:  # center (default)
            video_filter = "crop=ih*9/16:ih,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

        # Добавляем текстовые оверлеи с настройками если указаны
        if title_text:
            # Настройки заголовка (title) - появляется в начале с fade эффектом
            # Оптимальные значения по умолчанию для Shorts (1080x1920)
            title_fontfile = title_config.get('fontfile')              # Опционально: путь к файлу шрифта
            title_font = title_config.get('font')                      # Опционально: имя системного шрифта
            title_fontsize = title_config.get('fontsize', 70)          # Крупный размер для заголовка
            title_fontcolor = title_config.get('fontcolor', 'white')   # Универсальный белый цвет
            title_bordercolor = title_config.get('bordercolor', 'black')  # Чёрная обводка для контраста
            title_borderw = title_config.get('borderw', 3)             # Достаточная обводка
            title_y = title_config.get('y', 150)                       # Отступ от верха
            title_start = title_config.get('start_time', 0.5)          # Когда появляется
            title_duration = title_config.get('duration', 4)           # Как долго показывается
            title_fade_in = title_config.get('fade_in', 0.5)           # Длительность fade in
            title_fade_out = title_config.get('fade_out', 0.5)         # Длительность fade out

            # Автоматический перенос текста заголовка если он длинный
            # Для fontsize 60: ~14 символов на строку
            max_chars_per_line_title = int(950 / (title_fontsize * 0.55))
            if len(title_text) > max_chars_per_line_title:
                words = title_text.split(' ')
                lines = []
                current_line = []
                current_length = 0

                for word in words:
                    word_len = len(word) + 1  # +1 для пробела
                    if current_length + word_len > max_chars_per_line_title and current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = word_len
                    else:
                        current_line.append(word)
                        current_length += word_len

                if current_line:
                    lines.append(' '.join(current_line))

                # FFmpeg поддерживает \n в тексте напрямую
                title_text = '\n'.join(lines[:2])  # Максимум 2 строки

            # Экранируем спецсимволы, \n экранируем как \\n для expansion
            title_escaped = title_text.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'").replace(',', '\\,')

            title_end = title_start + title_duration
            fade_in_end = title_start + title_fade_in
            fade_out_start = title_end - title_fade_out

            # Извлекаем text_align (по умолчанию center для многострочного текста)
            title_text_align = title_config.get('text_align', 'center')

            # Формируем drawtext фильтр
            drawtext_params = [
                f"text='{title_escaped}'",
                "expansion=normal",
                f"text_align={title_text_align}"
            ]

            # Добавляем font или fontfile (fontfile имеет приоритет)
            if title_fontfile:
                fontfile_escaped = title_fontfile.replace(':', '\\:').replace("'", "\\'")
                drawtext_params.append(f"fontfile='{fontfile_escaped}'")
            elif title_font:
                font_escaped = title_font.replace(':', '\\:').replace("'", "\\'")
                drawtext_params.append(f"font='{font_escaped}'")

            drawtext_params.extend([
                f"fontsize={title_fontsize}",
                f"fontcolor={title_fontcolor}",
                f"bordercolor={title_bordercolor}",
                f"borderw={title_borderw}",
                f"x=(w-text_w)/2",
                f"y={title_y}",
                f"enable='between(t\\,{title_start}\\,{title_end})'",
                f"alpha='if(lt(t\\,{fade_in_end})\\,(t-{title_start})/{title_fade_in}\\,if(gt(t\\,{fade_out_start})\\,({title_end}-t)/{title_fade_out}\\,1))'"
            ])

            video_filter += f",drawtext={':'.join(drawtext_params)}"

        # Динамические субтитры - каждый сегмент со своими таймкодами
        if subtitles:
            # Настройки субтитров (subtitle) - появляются внизу экрана
            # Оптимальные значения по умолчанию для Shorts (1080x1920)
            subtitle_fontfile = subtitle_config.get('fontfile')               # Опционально: путь к файлу шрифта
            subtitle_font = subtitle_config.get('font')                       # Опционально: имя системного шрифта
            subtitle_fontsize = subtitle_config.get('fontsize', 60)           # Крупный размер для читаемости
            subtitle_fontcolor = subtitle_config.get('fontcolor', 'white')    # Белый цвет для читаемости
            subtitle_bordercolor = subtitle_config.get('bordercolor', 'black')  # Чёрная обводка для контраста
            subtitle_borderw = subtitle_config.get('borderw', 3)              # Достаточная обводка
            subtitle_y = subtitle_config.get('y', 'h-200')                    # Отступ от низа
            subtitle_text_align = subtitle_config.get('text_align', 'center') # Выравнивание по центру

            for subtitle in subtitles:
                sub_text = subtitle.get('text', '')
                sub_start = subtitle.get('start', 0)
                sub_end = subtitle.get('end', 0)

                if sub_text and sub_start is not None and sub_end is not None:
                    # Автоматический перенос текста если он длинный
                    # Для fontsize 64: ~12 символов на строку, для 48: ~16 символов (уменьшен для надёжности)
                    max_chars_per_line = int(950 / (subtitle_fontsize * 0.55))  # Более консервативный расчёт
                    if len(sub_text) > max_chars_per_line:
                        words = sub_text.split(' ')
                        lines = []
                        current_line = []
                        current_length = 0

                        for word in words:
                            word_len = len(word) + 1  # +1 для пробела
                            if current_length + word_len > max_chars_per_line and current_line:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                                current_length = word_len
                            else:
                                current_line.append(word)
                                current_length += word_len

                        if current_line:
                            lines.append(' '.join(current_line))

                        # FFmpeg поддерживает \n в тексте напрямую
                        sub_text = '\n'.join(lines[:2])  # Максимум 2 строки

                    # Экранируем текст, \n экранируем как \\n для expansion
                    sub_escaped = sub_text.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'").replace(',', '\\,')

                    # Формируем drawtext фильтр для субтитров
                    sub_drawtext_params = [
                        f"text='{sub_escaped}'",
                        "expansion=normal",
                        f"text_align={subtitle_text_align}"
                    ]

                    # Добавляем font или fontfile (fontfile имеет приоритет)
                    if subtitle_fontfile:
                        subfontfile_escaped = subtitle_fontfile.replace(':', '\\:').replace("'", "\\'")
                        sub_drawtext_params.append(f"fontfile='{subfontfile_escaped}'")
                    elif subtitle_font:
                        subfont_escaped = subtitle_font.replace(':', '\\:').replace("'", "\\'")
                        sub_drawtext_params.append(f"font='{subfont_escaped}'")

                    sub_drawtext_params.extend([
                        f"fontsize={subtitle_fontsize}",
                        f"fontcolor={subtitle_fontcolor}",
                        f"bordercolor={subtitle_bordercolor}",
                        f"borderw={subtitle_borderw}",
                        f"x=(w-text_w)/2",
                        f"y={subtitle_y}",
                        f"enable='between(t\\,{sub_start}\\,{sub_end})'"
                    ])

                    video_filter += f",drawtext={':'.join(sub_drawtext_params)}"

        update_task(task_id, {'progress': 40})

        # FFmpeg обработка
        logger.info(f"Task {task_id}: Processing video with FFmpeg")
        cmd = [
            'ffmpeg',
            '-ss', start_str,
            '-i', input_path,
        ]

        if duration_str:
            cmd.extend(['-t', duration_str])
        else:
            cmd.extend(['-to', str(end_time)])

        cmd.extend([
            '-filter_complex' if crop_mode == 'letterbox' else '-vf', video_filter,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',
            output_path
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"FFmpeg error: {result.stderr}")

        os.chmod(output_path, 0o644)
        update_task(task_id, {'progress': 90})

        # Удаляем входной файл
        if os.path.exists(input_path):
            os.remove(input_path)

        file_size = os.path.getsize(output_path)
        
        # Сохраняем метаданные
        metadata = {
            'task_id': task_id,
            'status': 'completed',
            'output_files': [{
                'filename': output_filename,
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'download_url': f"http://video-processor:5001/download/{task_id}/output/{output_filename}",
                'download_path': f"/download/{task_id}/output/{output_filename}"
            }],
            'total_files': 1,
            'total_size': file_size,
            'total_size_mb': round(file_size / (1024 * 1024), 2),
            'created_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'ttl_seconds': 7200,
            'ttl_human': '2 hours'
        }
        save_task_metadata(task_id, metadata)

        # Обновляем задачу
        update_task(task_id, {
            'status': 'completed',
            'progress': 100,
            'filename': output_filename,
            'file_size': file_size,
            'download_path': f"/download/{task_id}/output/{output_filename}",
            'download_url': f"http://video-processor:5001/download/{task_id}/output/{output_filename}",
            'metadata_url': f"http://video-processor:5001/download/{task_id}/metadata.json",
            'completed_at': datetime.now().isoformat()
        })

        logger.info(f"Task {task_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Task {task_id}: Error - {e}")
        update_task(task_id, {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })

def generate_shorts_async():
    """Внутренняя функция для асинхронной генерации Shorts"""
    data = request.json
    if not data:
        return jsonify({"success": False, "error": "JSON data required"}), 400

    # Подготавливаем параметры через общую функцию
    params = prepare_video_params(data)

    # Валидация обязательных параметров
    if not all([params['video_url'], params['start_time'] is not None, params['end_time'] is not None]):
        return jsonify({
            "success": False,
            "error": "video_url, start_time, and end_time are required"
        }), 400

    # Создаём задачу
    task_id = str(uuid.uuid4())
    task_data = {
        'task_id': task_id,
        'status': 'queued',
        'progress': 0,
        'video_url': params['video_url'],
        'start_time': params['start_time'],
        'end_time': params['end_time'],
        'crop_mode': params['crop_mode'],
        'title_text': params['title_text'],
        'subtitles': params['subtitles'],
        'title_config': params['title_config'],
        'subtitle_config': params['subtitle_config'],
        'created_at': datetime.now().isoformat()
    }
    save_task(task_id, task_data)

    # Запускаем фоновую обработку
    thread = threading.Thread(
        target=process_video_background,
        args=(task_id, params['video_url'], params['start_time'], params['end_time'], params['crop_mode'],
              params['title_text'], params['subtitles'], params['title_config'], params['subtitle_config'])
    )
    thread.daemon = True
    thread.start()

    logger.info(f"Task {task_id}: Created and started")

    return jsonify({
        "success": True,
        "task_id": task_id,
        "status": "queued",
        "message": "Task created and processing started",
        "check_status_url": f"/task_status/{task_id}"
    }), 202

@app.route('/task_status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Получить статус задачи"""
    try:
        task = get_task(task_id)

        if not task:
            return jsonify({
                "success": False,
                "error": "Task not found"
            }), 404

        response = {
            "success": True,
            "task_id": task_id,
            "status": task['status'],
            "progress": task.get('progress', 0),
            "created_at": task.get('created_at')
        }

        if task['status'] == 'completed':
            response.update({
                'filename': task.get('filename'),
                'file_size': task.get('file_size'),
                'download_url': task.get('download_url'),
                'download_path': task.get('download_path'),
                'completed_at': task.get('completed_at')
            })
        elif task['status'] == 'failed':
            response.update({
                'error': task.get('error'),
                'failed_at': task.get('failed_at')
            })

        return jsonify(response)

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/tasks', methods=['GET'])
def list_all_tasks():
    """Получить список всех задач"""
    try:
        recent_tasks = list_tasks()
        return jsonify({
            "success": True,
            "total": len(recent_tasks),
            "tasks": recent_tasks,
            "storage_mode": STORAGE_MODE
        })
    except Exception as e:
        logger.error(f"List tasks error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/process_video', methods=['POST'])
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
            return jsonify({"success": False, "error": "JSON data required"}), 400

        # Базовые параметры
        video_url = data.get('video_url')
        execution = data.get('execution', 'sync')  # sync или async
        operations = data.get('operations', [])
        webhook_url = data.get('webhook_url', os.getenv('WEBHOOK_URL'))

        if not video_url:
            return jsonify({"success": False, "error": "video_url is required"}), 400

        if not operations:
            return jsonify({
                "success": False,
                "error": "operations list is required"
            }), 400

        # Валидация операций
        for op in operations:
            op_type = op.get('type')
            if not op_type:
                return jsonify({
                    "success": False,
                    "error": "Each operation must have 'type' field"
                }), 400

            if op_type not in OPERATIONS_REGISTRY:
                return jsonify({
                    "success": False,
                    "error": f"Unknown operation type: {op_type}. Available: {list(OPERATIONS_REGISTRY.keys())}"
                }), 400

            # Валидация параметров операции
            operation_handler = OPERATIONS_REGISTRY[op_type]
            is_valid, error_msg = operation_handler.validate(op)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": f"Operation '{op_type}' validation failed: {error_msg}"
                }), 400

        # Выполнение операций
        if execution == 'async':
            # Асинхронный режим
            task_id = str(uuid.uuid4())
            
            # Создаем директории для задачи
            create_task_dirs(task_id)
            
            task_data = {
                'task_id': task_id,
                'status': 'queued',
                'progress': 0,
                'video_url': video_url,
                'operations': operations,
                'webhook_url': webhook_url,
                'created_at': datetime.now().isoformat()
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

            return jsonify({
                "success": True,
                "task_id": task_id,
                "status": "processing",
                "message": "Task created and processing in background",
                "check_status_url": f"/task_status/{task_id}"
            }), 202

        else:
            # Синхронный режим
            task_id = str(uuid.uuid4())
            
            # Создаем директории для задачи
            create_task_dirs(task_id)
            
            return process_video_pipeline_sync(task_id, video_url, operations, webhook_url)

    except Exception as e:
        logger.error(f"Process video error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def process_video_pipeline_sync(task_id: str, video_url: str, operations: list, webhook_url: str = None) -> dict:
    """Синхронное выполнение pipeline операций"""
    import requests

    # Скачиваем исходное видео в input/
    input_filename = f"{uuid.uuid4()}.mp4"
    input_path = os.path.join(get_task_input_dir(task_id), input_filename)

    response = requests.get(video_url, stream=True)
    with open(input_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    current_input = input_path
    output_files = []  # Список всех созданных output файлов

    # Выполняем операции последовательно
    for idx, op_data in enumerate(operations):
        op_type = op_data['type']
        operation = OPERATIONS_REGISTRY[op_type]

        # Генерируем временный выходной файл
        if idx == len(operations) - 1:
            # Последняя операция - финальный файл в output/
            output_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(get_task_output_dir(task_id), output_filename)
        else:
            # Промежуточный файл в temp/
            output_path = os.path.join(get_task_temp_dir(task_id), f"temp_{idx}_{uuid.uuid4()}.mp4")

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
            return jsonify({"success": False, "error": message, "task_id": task_id}), 500
        
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
    input_dir = get_task_input_dir(task_id)
    temp_dir = get_task_temp_dir(task_id)
    if os.path.exists(input_dir):
        shutil.rmtree(input_dir)
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

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
                'chunk_index': idx + 1,
                'chunk_total': total,
                'chunk_label': f"{idx + 1}/{total}"
            }
    for file_path in output_files:
        if os.path.exists(file_path):
            os.chmod(file_path, 0o644)
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            download_path = f"/download/{task_id}/output/{filename}"
            
            entry = {
                "filename": filename,
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "download_path": download_path,
                "download_url": f"http://video-processor:5001{download_path}"
            }
            if filename in chunk_map:
                entry.update(chunk_map[filename])
            files_info.append(entry)

    # Сохраняем metadata
    metadata = {
        "task_id": task_id,
        "status": "completed",
        "video_url": video_url,
        "operations": operations,
        "output_files": files_info,
        "total_files": len(files_info),
        "completed_at": datetime.now().isoformat()
    }
    save_task_metadata(task_id, metadata)

    # Отправляем webhook если указан
    if webhook_url:
        webhook_payload = {
            "task_id": task_id,
            "event": "task_completed",
            "status": "completed",
            "output_files": files_info,
            "total_files": len(files_info),
            "metadata_url": f"http://video-processor:5001/download/{task_id}/metadata.json",
            "completed_at": metadata["completed_at"]
        }
        send_webhook(webhook_url, webhook_payload)

    return jsonify({
        "success": True,
        "task_id": task_id,
        "status": "completed",
        "output_files": files_info,
        "total_files": len(files_info),
        "metadata_url": f"/download/{task_id}/metadata.json",
        "note": "Files will auto-delete after 2 hours.",
        "completed_at": metadata["completed_at"]
    })


def process_video_pipeline_background(task_id: str, video_url: str, operations: list, webhook_url: str = None):
    """Фоновое выполнение pipeline операций с использованием task-based архитектуры"""
    import requests

    try:
        # Создаем директории для задачи
        create_task_dirs(task_id)
        
        update_task(task_id, {'status': 'processing', 'progress': 5})

        # Скачиваем исходное видео в input директорию
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(get_task_input_dir(task_id), input_filename)

        logger.info(f"Task {task_id}: Downloading video from {video_url}")
        response = requests.get(video_url, stream=True, timeout=300)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

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
                # Последняя операция - в output директорию
                output_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}.mp4"
                output_path = os.path.join(get_task_output_dir(task_id), output_filename)
            else:
                # Промежуточный файл - в temp директорию
                output_path = os.path.join(get_task_temp_dir(task_id), f"temp_{idx}_{uuid.uuid4()}.mp4")

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
                    'chunk_index': idx + 1,
                    'chunk_total': total,
                    'chunk_label': f"{idx + 1}/{total}"
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
                    'download_url': f"http://video-processor:5001/download/{task_id}/output/{filename}",
                    'download_path': f"/download/{task_id}/output/{filename}"
                }
                if filename in chunk_map:
                    entry.update(chunk_map[filename])
                output_files_info.append(entry)

        # Сохраняем метаданные
        metadata = {
            'task_id': task_id,
            'status': 'completed',
            'operations': operations,
            'operations_count': total_ops,
            'output_files': output_files_info,
            'total_files': len(output_files_info),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'created_at': datetime.now().isoformat(),
            'completed_at': datetime.now().isoformat(),
            'ttl_seconds': 7200,
            'ttl_human': '2 hours'
        }
        save_task_metadata(task_id, metadata)

        # Обновляем задачу
        update_task(task_id, {
            'status': 'completed',
            'progress': 100,
            'output_files': output_files_info,
            'total_files': len(output_files_info),
            'total_size': total_size,
            'metadata_url': f"http://video-processor:5001/download/{task_id}/metadata.json",
            'operations_executed': total_ops,
            'completed_at': datetime.now().isoformat()
        })

        logger.info(f"Task {task_id}: Completed successfully with {len(output_files_info)} output file(s)")

        # Отправляем финальный webhook если указан
        if webhook_url:
            webhook_payload = {
                'task_id': task_id,
                'event': 'task_completed',
                'status': 'completed',
                'output_files': output_files_info,
                'total_files': len(output_files_info),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'metadata_url': f"http://video-processor:5001/download/{task_id}/metadata.json",
                'file_ttl_seconds': 7200,
                'file_ttl_human': '2 hours',
                'operations_executed': total_ops,
                'completed_at': datetime.now().isoformat()
            }
            send_webhook(webhook_url, webhook_payload)

    except Exception as e:
        logger.error(f"Task {task_id}: Error - {e}")
        update_task(task_id, {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })

        # Отправляем error webhook если указан
        if webhook_url:
            error_payload = {
                'task_id': task_id,
                'event': 'task_failed',
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.now().isoformat()
            }
            send_webhook(webhook_url, error_payload)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
