from flask import Flask, request, jsonify, send_file
import os
import subprocess
from datetime import datetime
import uuid
import logging
import threading
from typing import Dict, Any
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
UPLOAD_DIR = "/app/uploads"
OUTPUT_DIR = "/app/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    """Удаляет файлы старше 2 часов"""
    import time
    current_time = time.time()
    try:
        for directory in [UPLOAD_DIR, OUTPUT_DIR]:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if not os.path.isfile(file_path):
                    continue
                if current_time - os.path.getmtime(file_path) > 7200:  # 2 часа
                    os.remove(file_path)
                    logger.info(f"Cleaned up old file: {filename}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


def download_additional_inputs(additional_inputs_urls: dict) -> dict:
    """
    Скачивает дополнительные входные данные (аудио, изображения и т.д.)

    Args:
        additional_inputs_urls: Словарь {name: url}

    Returns:
        Словарь {name: local_path} с локальными путями к скачанным файлам
    """
    import requests

    additional_inputs_paths = {}

    for name, url in additional_inputs_urls.items():
        try:
            # Определяем расширение файла из URL
            ext = url.split('.')[-1].split('?')[0]
            if ext not in ['mp3', 'wav', 'aac', 'm4a', 'png', 'jpg', 'jpeg', 'gif', 'mp4']:
                ext = 'bin'

            # Скачиваем файл
            filename = f"additional_{name}_{uuid.uuid4()}.{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            logger.info(f"Downloading additional input '{name}' from {url}")
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            additional_inputs_paths[name] = file_path
            logger.info(f"Downloaded additional input '{name}' to {file_path}")

        except Exception as e:
            logger.error(f"Failed to download additional input '{name}': {e}")
            raise Exception(f"Failed to download additional input '{name}': {e}")

    return additional_inputs_paths


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
        title_text = params.get('title_text', '')

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

        # Конфигурации с оптимальными fallback для Shorts
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
    """Операция извлечения аудио"""
    def __init__(self):
        super().__init__(
            name="extract_audio",
            required_params=[],
            optional_params={
                'format': 'mp3',
                'bitrate': '192k'
            }
        )

    def execute(self, input_path: str, output_path: str, params: dict, additional_inputs: dict = None) -> tuple[bool, str]:
        """Извлечение аудио из видео"""
        audio_format = params.get('format', 'mp3')
        bitrate = params.get('bitrate', '192k')

        # Меняем расширение выходного файла
        output_audio = output_path.rsplit('.', 1)[0] + f'.{audio_format}'

        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vn',  # Без видео
            '-acodec', 'libmp3lame' if audio_format == 'mp3' else 'aac',
            '-b:a', bitrate,
            '-y',
            output_audio
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"FFmpeg error: {result.stderr}"

        return True, f"Audio extracted to {audio_format}"


# Регистрация всех операций
OPERATIONS_REGISTRY = {
    'cut': CutOperation(),
    'to_shorts': ToShortsOperation(),
    'extract_audio': ExtractAudioOperation(),
}


def validate_ffmpeg_params(params: dict) -> tuple[bool, str]:
    """Валидация параметров FFmpeg для безопасности"""
    # Whitelist разрешённых параметров
    ALLOWED_INPUT_OPTIONS = {'-ss', '-t', '-to', '-f', '-r', '-s'}
    ALLOWED_OUTPUT_OPTIONS = {
        '-c:v', '-c:a', '-preset', '-crf', '-b:v', '-b:a',
        '-vf', '-af', '-filter_complex', '-movflags',
        '-r', '-s', '-ar', '-ac'
    }
    DANGEROUS_PATTERNS = ['../', '/etc/', '/root/', '$(', '`', '|', '&&', '||', ';']

    # Проверка input_options
    if 'input_options' in params:
        for option in params['input_options']:
            # Проверка на опасные паттерны
            for pattern in DANGEROUS_PATTERNS:
                if pattern in str(option):
                    return False, f"Dangerous pattern detected: {pattern}"

            # Проверка первого параметра (должен быть из whitelist)
            if option.startswith('-') and option not in ALLOWED_INPUT_OPTIONS:
                return False, f"Input option not allowed: {option}"

    # Проверка output_options
    if 'output_options' in params:
        for option in params['output_options']:
            if option.startswith('-') and option not in ALLOWED_OUTPUT_OPTIONS:
                return False, f"Output option not allowed: {option}"

    return True, ""

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

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Скачать обработанный файл"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
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
    """Фоновая обработка видео"""
    if title_config is None:
        title_config = {}
    if subtitle_config is None:
        subtitle_config = {}
    if subtitles is None:
        subtitles = []
    try:
        update_task(task_id, {'status': 'processing', 'progress': 0})

        # Скачиваем видео
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(UPLOAD_DIR, input_filename)

        logger.info(f"Task {task_id}: Downloading video from {video_url}")
        import requests
        response = requests.get(video_url, stream=True, timeout=300)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        update_task(task_id, {'progress': 30})

        # Создаём выходной файл
        output_filename = f"shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

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
        download_path = f"/download/{output_filename}"

        # Обновляем задачу
        update_task(task_id, {
            'status': 'completed',
            'progress': 100,
            'filename': output_filename,
            'file_size': file_size,
            'download_path': download_path,
            'download_url': f"http://video-processor:5001{download_path}",
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
    Универсальный endpoint для обработки видео

    Поддерживает:
    - Простой режим: operations (cut, to_shorts, extract_audio)
    - Advanced режим: raw FFmpeg команды
    - Pipeline обработки (цепочка операций)
    - Sync/Async режимы

    Пример запроса (простой режим):
    {
      "async": true,
      "video_url": "https://...",
      "operations": [
        {"type": "cut", "start_time": 10, "end_time": 20},
        {"type": "to_shorts", "crop_mode": "center"}
      ]
    }

    Пример запроса (advanced режим):
    {
      "async": false,
      "video_url": "https://...",
      "mode": "advanced",
      "ffmpeg": {
        "input_options": ["-ss", "10"],
        "video_filters": ["scale=1080:1920"],
        "output_options": ["-c:v", "libx264", "-crf", "23"]
      }
    }
    """
    try:
        cleanup_old_files()

        data = request.json
        if not data:
            return jsonify({"success": False, "error": "JSON data required"}), 400

        # Базовые параметры
        video_url = data.get('video_url')
        is_async = data.get('async', False)
        mode = data.get('mode', 'simple')  # simple или advanced
        webhook_url = data.get('webhook_url', os.getenv('WEBHOOK_URL'))
        additional_inputs_urls = data.get('additional_inputs', {})  # {name: url}

        if not video_url:
            return jsonify({"success": False, "error": "video_url is required"}), 400

        # Обработка в зависимости от режима
        if mode == 'advanced':
            # Advanced режим - raw FFmpeg команды
            ffmpeg_params = data.get('ffmpeg', {})

            if not ffmpeg_params:
                return jsonify({
                    "success": False,
                    "error": "ffmpeg parameters are required for advanced mode"
                }), 400

            # Валидация FFmpeg параметров
            is_valid, error_msg = validate_ffmpeg_params(ffmpeg_params)
            if not is_valid:
                return jsonify({"success": False, "error": error_msg}), 400

            # Выполняем raw FFmpeg команды (только sync режим)
            return execute_ffmpeg_advanced(video_url, ffmpeg_params, additional_inputs_urls)

        else:
            # Простой режим - операции
            operations = data.get('operations', [])

            if not operations:
                return jsonify({
                    "success": False,
                    "error": "operations list is required for simple mode"
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
            if is_async:
                # Асинхронный режим
                task_id = str(uuid.uuid4())
                task_data = {
                    'task_id': task_id,
                    'status': 'queued',
                    'progress': 0,
                    'video_url': video_url,
                    'operations': operations,
                    'additional_inputs': additional_inputs_urls,
                    'webhook_url': webhook_url,
                    'created_at': datetime.now().isoformat()
                }
                save_task(task_id, task_data)

                # Запускаем фоновую обработку
                thread = threading.Thread(
                    target=process_video_pipeline_background,
                    args=(task_id, video_url, operations, webhook_url, additional_inputs_urls)
                )
                thread.daemon = True
                thread.start()

                logger.info(f"Task {task_id}: Created with {len(operations)} operations")

                return jsonify({
                    "success": True,
                    "task_id": task_id,
                    "status": "queued",
                    "operations_count": len(operations),
                    "additional_inputs_count": len(additional_inputs_urls),
                    "message": "Task created and processing started",
                    "check_status_url": f"/task_status/{task_id}"
                }), 202

            else:
                # Синхронный режим
                return process_video_pipeline_sync(video_url, operations, additional_inputs_urls)

    except Exception as e:
        logger.error(f"Process video error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def execute_ffmpeg_advanced(video_url: str, ffmpeg_params: dict, additional_inputs_urls: dict = None) -> dict:
    """
    Выполнение raw FFmpeg команд (advanced режим)

    Args:
        video_url: URL исходного видео
        ffmpeg_params: Параметры FFmpeg {
            'input_options': ['-ss', '10', '-t', '5'],
            'filter_complex': 'overlay=W-w-10:10',  # для наложения
            'video_filters': ['scale=1080:1920', 'fps=30'],
            'audio_filters': ['volume=2.0'],
            'output_options': ['-c:v', 'libx264', '-crf', '23']
        }
        additional_inputs_urls: Дополнительные входные файлы {
            'logo': 'https://logo.png',
            'background_audio': 'https://music.mp3'
        }

    Returns:
        JSON response с результатом
    """
    import requests

    additional_inputs_urls = additional_inputs_urls or {}

    # Скачиваем дополнительные входные данные
    additional_inputs_paths = {}
    if additional_inputs_urls:
        logger.info(f"Advanced mode: Downloading {len(additional_inputs_urls)} additional inputs")
        additional_inputs_paths = download_additional_inputs(additional_inputs_urls)

    # Скачиваем исходное видео
    input_filename = f"{uuid.uuid4()}.mp4"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    logger.info(f"Advanced mode: Downloading video from {video_url}")
    response = requests.get(video_url, stream=True, timeout=300)
    with open(input_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    # Формируем выходной файл
    output_filename = f"advanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # Строим FFmpeg команду
    cmd = ['ffmpeg']

    # Input options (перед -i)
    input_options = ffmpeg_params.get('input_options', [])
    if input_options:
        cmd.extend(input_options)

    # Основное видео всегда первое
    cmd.extend(['-i', input_path])

    # Добавляем дополнительные входы (для overlay, amix и т.д.)
    for name, path in additional_inputs_paths.items():
        cmd.extend(['-i', path])

    # Filter complex (для сложных фильтров с несколькими входами)
    filter_complex = ffmpeg_params.get('filter_complex')
    if filter_complex:
        # Заменяем placeholders на индексы FFmpeg
        # {input} -> [0:v] или [0:a]
        # {logo} -> [1:v] (первый дополнительный вход)
        # {background_music} -> [2:a] (второй дополнительный вход)

        # Маппинг: название -> индекс
        input_mapping = {'input': 0}
        for idx, name in enumerate(additional_inputs_paths.keys(), start=1):
            input_mapping[name] = idx

        # Заменяем placeholders
        for name, index in input_mapping.items():
            filter_complex = filter_complex.replace(f'{{{name}:v}}', f'[{index}:v]')
            filter_complex = filter_complex.replace(f'{{{name}:a}}', f'[{index}:a]')
            filter_complex = filter_complex.replace(f'{{{name}}}', f'[{index}]')

        cmd.extend(['-filter_complex', filter_complex])
    else:
        # Video filters (простые)
        video_filters = ffmpeg_params.get('video_filters', [])
        if video_filters:
            vf_string = ','.join(video_filters)
            cmd.extend(['-vf', vf_string])

        # Audio filters (простые)
        audio_filters = ffmpeg_params.get('audio_filters', [])
        if audio_filters:
            af_string = ','.join(audio_filters)
            cmd.extend(['-af', af_string])

    # Output options
    output_options = ffmpeg_params.get('output_options', [])
    if output_options:
        cmd.extend(output_options)

    # Финальные параметры
    cmd.extend(['-y', output_path])

    logger.info(f"Advanced mode: Executing FFmpeg: {' '.join(cmd)}")

    # Выполняем команду
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Удаляем входной файл и дополнительные входы
    if os.path.exists(input_path):
        os.remove(input_path)

    for name, path in additional_inputs_paths.items():
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Advanced mode: Cleaned up additional input: {name}")

    if result.returncode != 0:
        logger.error(f"Advanced mode FFmpeg error: {result.stderr}")
        return jsonify({"success": False, "error": f"FFmpeg error: {result.stderr}"}), 500

    # Результат
    os.chmod(output_path, 0o644)
    file_size = os.path.getsize(output_path)

    download_path = f"/download/{output_filename}"
    base_url = request.host_url.rstrip('/')
    full_download_url = f"{base_url}{download_path}"

    return jsonify({
        "success": True,
        "mode": "advanced",
        "filename": output_filename,
        "file_path": output_path,
        "file_size": file_size,
        "file_size_mb": round(file_size / (1024 * 1024), 2),
        "download_url": full_download_url,
        "download_path": download_path,
        "ffmpeg_command": ' '.join(cmd),
        "note": "File will auto-delete after 2 hours.",
        "processed_at": datetime.now().isoformat()
    })


def process_video_pipeline_sync(video_url: str, operations: list, additional_inputs_urls: dict = None) -> dict:
    """Синхронное выполнение pipeline операций"""
    import requests

    additional_inputs_urls = additional_inputs_urls or {}

    # Скачиваем дополнительные входные данные (если указаны)
    additional_inputs_paths = {}
    if additional_inputs_urls:
        logger.info(f"Downloading {len(additional_inputs_urls)} additional inputs")
        additional_inputs_paths = download_additional_inputs(additional_inputs_urls)

    # Скачиваем исходное видео
    input_filename = f"{uuid.uuid4()}.mp4"
    input_path = os.path.join(UPLOAD_DIR, input_filename)

    response = requests.get(video_url, stream=True)
    with open(input_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    current_input = input_path
    final_output = None

    # Выполняем операции последовательно
    for idx, op_data in enumerate(operations):
        op_type = op_data['type']
        operation = OPERATIONS_REGISTRY[op_type]

        # Генерируем временный выходной файл
        if idx == len(operations) - 1:
            # Последняя операция - финальный файл
            output_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            final_output = output_path
        else:
            # Промежуточный файл
            output_path = os.path.join(UPLOAD_DIR, f"temp_{idx}_{uuid.uuid4()}.mp4")

        logger.info(f"Executing operation {idx+1}/{len(operations)}: {op_type}")

        # Выполняем операцию с additional_inputs
        success, message = operation.execute(current_input, output_path, op_data, additional_inputs_paths)

        if not success:
            # Ошибка - удаляем временные файлы
            if os.path.exists(input_path):
                os.remove(input_path)
            return jsonify({"success": False, "error": message}), 500

        # Удаляем предыдущий временный файл
        if current_input != input_path and os.path.exists(current_input):
            os.remove(current_input)

        # Следующая операция будет использовать этот файл как вход
        current_input = output_path

    # Удаляем исходный файл и дополнительные входные данные
    if os.path.exists(input_path):
        os.remove(input_path)

    for name, path in additional_inputs_paths.items():
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Cleaned up additional input: {name}")

    # Финальный результат
    os.chmod(final_output, 0o644)
    file_size = os.path.getsize(final_output)

    download_path = f"/download/{os.path.basename(final_output)}"
    base_url = request.host_url.rstrip('/')
    full_download_url = f"{base_url}{download_path}"

    return jsonify({
        "success": True,
        "filename": os.path.basename(final_output),
        "file_path": final_output,
        "file_size": file_size,
        "download_url": full_download_url,
        "download_path": download_path,
        "operations_executed": len(operations),
        "note": "File will auto-delete after 2 hours.",
        "processed_at": datetime.now().isoformat()
    })


def process_video_pipeline_background(task_id: str, video_url: str, operations: list, webhook_url: str = None, additional_inputs_urls: dict = None):
    """Фоновое выполнение pipeline операций"""
    import requests

    additional_inputs_urls = additional_inputs_urls or {}

    try:
        update_task(task_id, {'status': 'processing', 'progress': 5})

        # Скачиваем дополнительные входные данные (если указаны)
        additional_inputs_paths = {}
        if additional_inputs_urls:
            logger.info(f"Task {task_id}: Downloading {len(additional_inputs_urls)} additional inputs")
            additional_inputs_paths = download_additional_inputs(additional_inputs_urls)

        # Скачиваем исходное видео
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(UPLOAD_DIR, input_filename)

        logger.info(f"Task {task_id}: Downloading video from {video_url}")
        response = requests.get(video_url, stream=True, timeout=300)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        update_task(task_id, {'progress': 20})

        current_input = input_path
        final_output = None

        # Выполняем операции последовательно
        total_ops = len(operations)
        for idx, op_data in enumerate(operations):
            op_type = op_data['type']
            operation = OPERATIONS_REGISTRY[op_type]

            # Прогресс: 20% + (idx / total_ops) * 70%
            progress = 20 + int((idx / total_ops) * 70)
            update_task(task_id, {'progress': progress, 'current_operation': op_type})

            # Генерируем временный выходной файл
            if idx == total_ops - 1:
                # Последняя операция - финальный файл
                output_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_id[:8]}.mp4"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                final_output = output_path
            else:
                # Промежуточный файл
                output_path = os.path.join(UPLOAD_DIR, f"temp_{idx}_{uuid.uuid4()}.mp4")

            logger.info(f"Task {task_id}: Executing operation {idx+1}/{total_ops}: {op_type}")

            # Выполняем операцию с additional_inputs
            success, message = operation.execute(current_input, output_path, op_data, additional_inputs_paths)

            if not success:
                raise Exception(f"Operation '{op_type}' failed: {message}")

            # Operation-level webhook (опционально)
            operation_webhook_url = op_data.get('webhook_url')
            if operation_webhook_url:
                operation_file_size = os.path.getsize(output_path)
                operation_payload = {
                    'task_id': task_id,
                    'event': 'operation_completed',
                    'operation_index': idx + 1,
                    'operation_total': total_ops,
                    'operation_type': op_type,
                    'operation_status': 'success',
                    'operation_message': message,
                    'file_size': operation_file_size,
                    'timestamp': datetime.now().isoformat()
                }
                send_webhook(operation_webhook_url, operation_payload)

            # Удаляем предыдущий временный файл
            if current_input != input_path and os.path.exists(current_input):
                os.remove(current_input)

            # Следующая операция будет использовать этот файл как вход
            current_input = output_path

        # Удаляем исходный файл и дополнительные входные данные
        if os.path.exists(input_path):
            os.remove(input_path)

        for name, path in additional_inputs_paths.items():
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Task {task_id}: Cleaned up additional input: {name}")

        # Финальный результат
        os.chmod(final_output, 0o644)
        update_task(task_id, {'progress': 95})

        file_size = os.path.getsize(final_output)
        download_path = f"/download/{os.path.basename(final_output)}"

        # Обновляем задачу
        update_task(task_id, {
            'status': 'completed',
            'progress': 100,
            'filename': os.path.basename(final_output),
            'file_size': file_size,
            'download_path': download_path,
            'download_url': f"http://video-processor:5001{download_path}",
            'operations_executed': total_ops,
            'completed_at': datetime.now().isoformat()
        })

        logger.info(f"Task {task_id}: Completed successfully")

        # Отправляем финальный webhook если указан
        if webhook_url:
            file_ttl_seconds = 7200  # 2 часа
            webhook_payload = {
                'task_id': task_id,
                'event': 'task_completed',
                'status': 'completed',
                'filename': os.path.basename(final_output),
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'file_ttl_seconds': file_ttl_seconds,
                'file_ttl_human': '2 hours',
                'download_path': download_path,
                'download_url': f"http://video-processor:5001{download_path}",
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
