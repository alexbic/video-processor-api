"""
Bootstrap Module - Unified infrastructure utilities for video processing APIs

This module provides infrastructure-level utilities for application startup,
dependency checking, and service initialization. Used by both youtube-downloader-api
and video-processor-api projects.

Responsibilities:
- Redis connection checking and retry logic
- TCP port connectivity verification
- Startup logging and configuration display
- Wait/retry mechanisms for external dependencies

Usage:
    from bootstrap import wait_for_redis, log_tcp_port, ensure_redis_connection
"""

import socket
import time
import logging
from typing import Callable, Optional


def wait_for_redis(
    check_fn: Callable[[], bool],
    retries: int = 6,
    delay: float = 0.5,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Repeatedly calls the provided check_fn() until success or retries exhausted.

    This function is used during application startup to wait for Redis to become
    available. It's critical for containerized deployments where Redis may take
    a few seconds to start.

    Args:
        check_fn: Callable that returns True on successful Redis connection
        retries: Number of retry attempts (default: 6)
        delay: Delay between retries in seconds (default: 0.5)
        logger: Optional logger for debug output

    Returns:
        True if check_fn succeeded, False if all retries exhausted

    Example:
        >>> def check_redis():
        ...     return redis_client.ping()
        >>> wait_for_redis(check_redis, retries=10, delay=1.0)
        True
    """
    for attempt in range(max(0, retries)):
        try:
            if check_fn():
                if logger:
                    logger.debug(f"wait_for_redis: succeeded on attempt {attempt + 1}/{retries}")
                return True
        except Exception as e:
            if logger:
                logger.debug(f"wait_for_redis: attempt {attempt + 1}/{retries} failed: {e}")

        # Don't sleep after last attempt
        if attempt < retries - 1:
            try:
                time.sleep(max(0.0, delay))
            except Exception:
                pass

    if logger:
        logger.warning(f"wait_for_redis: all {retries} attempts failed")
    return False


def log_tcp_port(
    logger: logging.Logger,
    host: str,
    port: int,
    timeout: float = 0.5,
    service_name: str = "Service"
) -> bool:
    """
    Checks TCP port connectivity and logs the result.

    Useful for verifying that dependent services (Redis, PostgreSQL, etc.)
    are accepting connections before the application starts.

    Args:
        logger: Logger instance for output
        host: Hostname or IP address
        port: TCP port number
        timeout: Connection timeout in seconds (default: 0.5)
        service_name: Name of service for log messages (default: "Service")

    Returns:
        True if connection successful, False otherwise

    Example:
        >>> log_tcp_port(logger, "localhost", 6379, service_name="Redis")
        True
        # Logs: "Redis TCP port (localhost:6379): OPEN"
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            logger.info(f"{service_name} TCP port ({host}:{port}): OPEN (connection possible)")
            return True
    except Exception as e:
        logger.warning(f"{service_name} TCP port ({host}:{port}): CLOSED (error: {e})")
        return False


def ensure_redis_connection(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    retries: int = 6,
    delay: float = 0.5,
    logger: Optional[logging.Logger] = None
) -> Optional[object]:
    """
    Establishes Redis connection with retry logic.

    This is a higher-level wrapper that combines Redis client creation
    with wait_for_redis retry logic. Returns None if connection fails.

    Args:
        host: Redis hostname (default: "localhost")
        port: Redis port (default: 6379)
        db: Redis database number (default: 0)
        retries: Number of connection attempts (default: 6)
        delay: Delay between attempts in seconds (default: 0.5)
        logger: Optional logger for output

    Returns:
        Redis client instance if successful, None otherwise

    Example:
        >>> client = ensure_redis_connection(
        ...     host="redis",
        ...     port=6379,
        ...     retries=10
        ... )
        >>> if client:
        ...     client.set("key", "value")
    """
    try:
        import redis  # type: ignore
    except ImportError:
        if logger:
            logger.error("Redis library not installed. Run: pip install redis")
        return None

    def check_connection() -> bool:
        """Internal check function for wait_for_redis"""
        try:
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            client.ping()
            return True
        except Exception:
            return False

    # Wait for Redis to become available
    if not wait_for_redis(check_connection, retries=retries, delay=delay, logger=logger):
        if logger:
            logger.error(f"Failed to connect to Redis at {host}:{port} after {retries} attempts")
        return None

    # Create and return the client
    try:
        client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        client.ping()
        if logger:
            logger.info(f"✓ Redis connected: {host}:{port} (db={db})")
        return client
    except Exception as e:
        if logger:
            logger.error(f"Failed to create Redis client: {e}")
        return None


def log_startup_banner(
    logger: logging.Logger,
    service_name: str,
    version: str,
    config: dict
) -> None:
    """
    Logs a startup banner with configuration details.

    Displays service name, version, and key configuration parameters
    in a formatted, easy-to-read banner.

    Args:
        logger: Logger instance for output
        service_name: Name of the service (e.g., "YouTube Downloader API")
        version: Version string (e.g., "1.2.0")
        config: Dictionary of configuration key-value pairs

    Example:
        >>> log_startup_banner(
        ...     logger,
        ...     "YouTube Downloader API",
        ...     "1.2.0",
        ...     {"workers": 2, "redis_host": "localhost", "auth": "enabled"}
        ... )
        # Logs formatted startup banner
    """
    banner_width = 60
    logger.info("=" * banner_width)
    logger.info(f"{service_name} v{version}".center(banner_width))
    logger.info("=" * banner_width)

    if config:
        logger.info("Configuration:")
        for key, value in config.items():
            # Format value for display
            if isinstance(value, bool):
                display_value = "enabled" if value else "disabled"
            else:
                display_value = str(value)
            logger.info(f"  {key}: {display_value}")

    logger.info("=" * banner_width)


def check_dependencies(
    dependencies: dict,
    logger: Optional[logging.Logger] = None
) -> dict:
    """
    Checks availability of multiple dependencies.

    Args:
        dependencies: Dict mapping service name to (host, port) tuple
        logger: Optional logger for output

    Returns:
        Dict mapping service name to bool (True if available)

    Example:
        >>> results = check_dependencies({
        ...     "Redis": ("localhost", 6379),
        ...     "PostgreSQL": ("localhost", 5432)
        ... })
        >>> print(results)
        {"Redis": True, "PostgreSQL": False}
    """
    results = {}
    for service_name, (host, port) in dependencies.items():
        available = log_tcp_port(
            logger if logger else logging.getLogger(__name__),
            host,
            port,
            service_name=service_name
        )
        results[service_name] = available
    return results


# Version info
BOOTSTRAP_VERSION = "1.2.0"
BOOTSTRAP_DATE = "2025-11-26"

__all__ = [
    "wait_for_redis",
    "log_tcp_port",
    "ensure_redis_connection",
    "log_startup_banner",
    "check_dependencies",
    "BOOTSTRAP_VERSION",
    "BOOTSTRAP_DATE"
]
