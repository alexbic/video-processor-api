from flask import Flask, request, jsonify, send_file
import os
import subprocess
from datetime import datetime
import uuid
import logging

app = Flask(__name__)

# Конфигурация
UPLOAD_DIR = "/app/uploads"
OUTPUT_DIR = "/app/outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "video-processor-api",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/extract_audio', methods=['POST'])
def extract_audio():
    """Извлечь аудио из видео с опциональным разбиением на чанки для Whisper API"""
    try:
        # Очистка старых файлов
        cleanup_old_files()

        data = request.json if request.json else {}

        # Проверяем наличие файла или URL
        if 'file' in request.files:
            # Загрузка файла напрямую
            video_file = request.files['file']
            input_filename = f"{uuid.uuid4()}.mp4"
            input_path = os.path.join(UPLOAD_DIR, input_filename)
            video_file.save(input_path)
        elif data.get('video_url'):
            # URL файла (от youtube-downloader-api)
            video_url = data.get('video_url')
            input_filename = f"{uuid.uuid4()}.mp4"
            input_path = os.path.join(UPLOAD_DIR, input_filename)

            # Скачиваем файл
            import requests
            response = requests.get(video_url, stream=True)
            with open(input_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            return jsonify({"success": False, "error": "No file or video_url provided"}), 400

        # Параметры чанков для Whisper API
        chunk_duration = data.get('chunk_duration_minutes')  # В минутах
        max_chunk_size_mb = data.get('max_chunk_size_mb', 24)  # По умолчанию 24 МБ

        # Формируем имя выходного аудио файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"audio_{timestamp}.mp3"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # FFmpeg команда для извлечения полного аудио
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vn',  # Отключаем видео
            '-acodec', 'libmp3lame',  # Кодек MP3
            '-q:a', '2',  # Качество аудио (0-9, 2 = высокое)
            '-y',  # Перезаписываем файл если существует
            output_path
        ]

        logger.info(f"Extracting audio: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return jsonify({"success": False, "error": result.stderr}), 500

        os.chmod(output_path, 0o644)
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)

        # Получаем длительность аудио
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            output_path
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
        total_duration = float(probe_result.stdout.strip())

        base_url = request.host_url.rstrip('/')
        chunks = []

        # Если указан chunk_duration или файл больше max_chunk_size_mb, разбиваем на чанки
        if chunk_duration or file_size_mb > max_chunk_size_mb:
            # Определяем длительность чанка
            if chunk_duration:
                # Пользователь указал длительность явно (приоритет)
                chunk_duration_seconds = chunk_duration * 60
            else:
                # Автоматически вычисляем длительность на основе целевого размера файла
                # При 64kbps: 1 секунда = 8 KB = 0.0078125 MB
                # Формула: max_chunk_size_mb / (64 kbps / 8 / 1024) = max_chunk_size_mb * 128
                # Добавляем запас 5% для безопасности
                chunk_duration_seconds = (max_chunk_size_mb * 128) * 0.95

            logger.info(f"Splitting audio into chunks of {chunk_duration_seconds/60:.1f} minutes (target size: {max_chunk_size_mb}MB)")

            # Разбиваем на чанки
            chunk_start = 0
            chunk_index = 0

            while chunk_start < total_duration:
                chunk_end = min(chunk_start + chunk_duration_seconds, total_duration)
                chunk_filename = f"audio_{timestamp}_chunk{chunk_index:03d}.mp3"
                chunk_path = os.path.join(OUTPUT_DIR, chunk_filename)

                chunk_duration_actual = chunk_end - chunk_start

                logger.info(f"Chunk {chunk_index}: duration={chunk_duration_actual:.1f}s, extracting from video...")

                # Извлекаем чанк напрямую из видео с фиксированным битрейтом
                # Все чанки будут иметь ОДИНАКОВОЕ качество (64kbps)
                chunk_cmd = [
                    'ffmpeg',
                    '-ss', str(chunk_start),  # Начало ПЕРЕД -i для быстрого seek
                    '-t', str(chunk_duration_actual),  # Длительность
                    '-i', input_path,  # Входное видео (не output_path!)
                    '-vn',  # Отключаем видео
                    '-acodec', 'libmp3lame',
                    '-b:a', '64k',  # Фиксированный битрейт для всех чанков
                    '-ar', '16000',  # 16kHz sample rate (оптимально для речи/Whisper)
                    '-ac', '1',  # Моно
                    '-y',
                    chunk_path
                ]

                chunk_result = subprocess.run(chunk_cmd, capture_output=True, text=True)

                if chunk_result.returncode != 0:
                    logger.error(f"Chunk {chunk_index} error: {chunk_result.stderr}")
                    continue

                os.chmod(chunk_path, 0o644)
                chunk_size = os.path.getsize(chunk_path)
                chunk_size_mb = chunk_size / (1024 * 1024)

                chunks.append({
                    "chunk_index": chunk_index,
                    "filename": chunk_filename,
                    "file_size": chunk_size,
                    "file_size_mb": round(chunk_size_mb, 2),
                    "start_time": round(chunk_start, 2),
                    "end_time": round(chunk_end, 2),
                    "duration": round(chunk_end - chunk_start, 2),
                    "download_url": f"{base_url}/download/{chunk_filename}",
                    "download_path": f"/download/{chunk_filename}",
                    "whisper_ready": chunk_size_mb <= 25
                })

                chunk_start = chunk_end
                chunk_index += 1

            logger.info(f"Created {len(chunks)} chunks")

            # Удаляем полный аудиофайл, оставляем только чанки
            if os.path.exists(output_path):
                os.remove(output_path)

            # Удаляем входной файл
            if os.path.exists(input_path):
                os.remove(input_path)

            return jsonify({
                "success": True,
                "mode": "chunked",
                "total_duration": round(total_duration, 2),
                "total_chunks": len(chunks),
                "chunk_duration_minutes": round(chunk_duration_seconds / 60, 1) if chunk_duration_seconds else None,
                "chunks": chunks,
                "note": f"Audio split into {len(chunks)} chunks. Each chunk optimized for Whisper API (<25MB). Files will auto-delete after 2 hours.",
                "processed_at": datetime.now().isoformat()
            })

        else:
            # Файл не требует разбиения - возвращаем как обычно
            download_path = f"/download/{output_filename}"
            full_download_url = f"{base_url}{download_path}"

            # Удаляем входной файл
            if os.path.exists(input_path):
                os.remove(input_path)

            return jsonify({
                "success": True,
                "mode": "single",
                "filename": output_filename,
                "file_path": output_path,
                "file_size": file_size,
                "file_size_mb": round(file_size_mb, 2),
                "duration": round(total_duration, 2),
                "download_url": full_download_url,
                "download_path": download_path,
                "whisper_ready": file_size_mb <= 25,
                "note": "Audio file will auto-delete after 2 hours." + ("" if file_size_mb <= 25 else f" Warning: File size ({file_size_mb:.1f}MB) exceeds Whisper API limit (25MB). Consider using chunk_duration parameter."),
                "processed_at": datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"Extract audio error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/cut_video', methods=['POST'])
def cut_video():
    """Нарезать видео по таймкодам"""
    try:
        cleanup_old_files()

        data = request.json
        if not data:
            return jsonify({"success": False, "error": "JSON data required"}), 400

        video_url = data.get('video_url')
        start_time = data.get('start_time')  # В секундах или формате HH:MM:SS
        end_time = data.get('end_time')      # В секундах или формате HH:MM:SS

        if not all([video_url, start_time is not None, end_time is not None]):
            return jsonify({
                "success": False,
                "error": "video_url, start_time, and end_time are required"
            }), 400

        # Скачиваем видео
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(UPLOAD_DIR, input_filename)

        import requests
        response = requests.get(video_url, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Формируем имя выходного файла
        output_filename = f"cut_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # Вычисляем длительность
        if isinstance(start_time, (int, float)) and isinstance(end_time, (int, float)):
            duration = end_time - start_time
            start_str = str(start_time)
            duration_str = str(duration)
        else:
            start_str = str(start_time)
            duration_str = None

        # FFmpeg команда для нарезки
        cmd = [
            'ffmpeg',
            '-ss', start_str,  # Начальная позиция
            '-i', input_path,
        ]

        if duration_str:
            cmd.extend(['-t', duration_str])  # Длительность
        else:
            cmd.extend(['-to', str(end_time)])

        cmd.extend([
            '-c', 'copy',  # Копируем без перекодирования (быстро)
            '-y',
            output_path
        ])

        logger.info(f"Cutting video: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return jsonify({"success": False, "error": result.stderr}), 500

        os.chmod(output_path, 0o644)
        file_size = os.path.getsize(output_path)

        download_path = f"/download/{output_filename}"
        base_url = request.host_url.rstrip('/')
        full_download_url = f"{base_url}{download_path}"

        # Удаляем входной файл
        if os.path.exists(input_path):
            os.remove(input_path)

        return jsonify({
            "success": True,
            "filename": output_filename,
            "file_path": output_path,
            "file_size": file_size,
            "download_url": full_download_url,
            "download_path": download_path,
            "start_time": start_time,
            "end_time": end_time,
            "note": "Video file will auto-delete after 2 hours.",
            "processed_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Cut video error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/convert_to_shorts', methods=['POST'])
def convert_to_shorts():
    """Конвертировать видео в формат Shorts (вертикальная ориентация 1080x1920)"""
    try:
        cleanup_old_files()

        data = request.json
        if not data:
            return jsonify({"success": False, "error": "JSON data required"}), 400

        video_url = data.get('video_url')
        crop_mode = data.get('crop_mode', 'center')  # center, top, bottom

        if not video_url:
            return jsonify({"success": False, "error": "video_url is required"}), 400

        # Скачиваем видео
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(UPLOAD_DIR, input_filename)

        import requests
        response = requests.get(video_url, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Формируем имя выходного файла
        output_filename = f"shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # Определяем фильтр обрезки в зависимости от режима
        if crop_mode == 'top':
            crop_filter = "crop=ih*9/16:ih:0:0"
        elif crop_mode == 'bottom':
            crop_filter = "crop=ih*9/16:ih:0:ih-oh"
        else:  # center
            crop_filter = "crop=ih*9/16:ih"

        # FFmpeg команда для конвертации в Shorts формат
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-vf', f"{crop_filter},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            '-c:v', 'libx264',  # H.264 кодек
            '-preset', 'medium',  # Баланс скорость/качество
            '-crf', '23',  # Качество (18-28, 23 = хорошее)
            '-c:a', 'aac',  # AAC аудио кодек
            '-b:a', '128k',  # Битрейт аудио
            '-movflags', '+faststart',  # Оптимизация для стриминга
            '-y',
            output_path
        ]

        logger.info(f"Converting to Shorts: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return jsonify({"success": False, "error": result.stderr}), 500

        os.chmod(output_path, 0o644)
        file_size = os.path.getsize(output_path)

        download_path = f"/download/{output_filename}"
        base_url = request.host_url.rstrip('/')
        full_download_url = f"{base_url}{download_path}"

        # Удаляем входной файл
        if os.path.exists(input_path):
            os.remove(input_path)

        return jsonify({
            "success": True,
            "filename": output_filename,
            "file_path": output_path,
            "file_size": file_size,
            "download_url": full_download_url,
            "download_path": download_path,
            "resolution": "1080x1920",
            "format": "shorts",
            "crop_mode": crop_mode,
            "note": "Shorts video will auto-delete after 2 hours.",
            "processed_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Convert to shorts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/process_to_shorts', methods=['POST'])
def process_to_shorts():
    """Комбинированный endpoint: нарезка + конвертация в Shorts за один запрос"""
    try:
        cleanup_old_files()

        data = request.json
        if not data:
            return jsonify({"success": False, "error": "JSON data required"}), 400

        video_url = data.get('video_url')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        crop_mode = data.get('crop_mode', 'center')

        if not all([video_url, start_time is not None, end_time is not None]):
            return jsonify({
                "success": False,
                "error": "video_url, start_time, and end_time are required"
            }), 400

        # Скачиваем видео
        input_filename = f"{uuid.uuid4()}.mp4"
        input_path = os.path.join(UPLOAD_DIR, input_filename)

        import requests
        response = requests.get(video_url, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        output_filename = f"shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
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
        if crop_mode == 'top':
            crop_filter = "crop=ih*9/16:ih:0:0"
        elif crop_mode == 'bottom':
            crop_filter = "crop=ih*9/16:ih:0:ih-oh"
        else:
            crop_filter = "crop=ih*9/16:ih"

        # Комбинированная FFmpeg команда: нарезка + конвертация
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
            '-vf', f"{crop_filter},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-movflags', '+faststart',
            '-y',
            output_path
        ])

        logger.info(f"Processing to Shorts: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return jsonify({"success": False, "error": result.stderr}), 500

        os.chmod(output_path, 0o644)
        file_size = os.path.getsize(output_path)

        download_path = f"/download/{output_filename}"
        base_url = request.host_url.rstrip('/')
        full_download_url = f"{base_url}{download_path}"

        # Удаляем входной файл
        if os.path.exists(input_path):
            os.remove(input_path)

        return jsonify({
            "success": True,
            "filename": output_filename,
            "file_path": output_path,
            "file_size": file_size,
            "download_url": full_download_url,
            "download_path": download_path,
            "resolution": "1080x1920",
            "format": "shorts",
            "crop_mode": crop_mode,
            "start_time": start_time,
            "end_time": end_time,
            "note": "Shorts video will auto-delete after 2 hours.",
            "processed_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Process to shorts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
