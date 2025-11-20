import socket
import time


def wait_for_redis(check_fn, retries=6, delay=0.5, logger=None):
    """Повторно вызывает переданную функцию check_fn() до успеха или исчерпания попыток.

    check_fn: callable -> bool (должна вернуть True при успешном подключении к Redis)
    retries: количество повторов
    delay: задержка между повторами в секундах
    logger: опциональный логгер
    """
    for _ in range(max(0, retries)):
        try:
            if check_fn():
                return True
        except Exception as e:
            if logger:
                logger.debug(f"wait_for_redis: check failed: {e}")
        try:
            time.sleep(max(0.0, delay))
        except Exception:
            pass
    return False


def log_tcp_port(logger, host: str, port: int, timeout: float = 0.5):
    """Лаконичная проверка доступности TCP-порта и логирование результата."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            logger.info("Redis TCP port: OPEN (connection possible)")
            return True
    except Exception:
        logger.info("Redis TCP port: CLOSED (no listener)")
        return False
