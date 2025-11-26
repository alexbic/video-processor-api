"""
API Commons - Unified utilities and error handling for video processing APIs

This module provides standardized error responses, constants, and utility functions
that are shared across youtube-downloader-api and video-processor-api projects.

Usage:
    from api_commons import (
        create_simple_error,
        create_task_error,
        create_internal_error,
        ERROR_INVALID_API_KEY,
        ERROR_TASK_NOT_FOUND
    )
"""

from datetime import datetime
from typing import Dict, Any, Optional


# ============================================
# ERROR CODE CONSTANTS (Unified Structure)
# ============================================

# Authentication & Authorization errors
ERROR_MISSING_AUTH_TOKEN = "MISSING_AUTH_TOKEN"
ERROR_INVALID_API_KEY = "INVALID_API_KEY"

# Validation errors
ERROR_MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
ERROR_INVALID_JSON = "INVALID_JSON"
ERROR_INVALID_URL = "INVALID_URL"
ERROR_INVALID_WEBHOOK_URL = "INVALID_WEBHOOK_URL"
ERROR_INVALID_WEBHOOK_HEADERS = "INVALID_WEBHOOK_HEADERS"
ERROR_INVALID_CLIENT_META = "INVALID_CLIENT_META"
ERROR_INVALID_OPERATION = "INVALID_OPERATION"

# Task errors
ERROR_TASK_NOT_FOUND = "TASK_NOT_FOUND"
ERROR_FILE_NOT_FOUND = "FILE_NOT_FOUND"
ERROR_INVALID_PATH = "INVALID_PATH"

# Download errors (youtube-downloader-api specific)
ERROR_VIDEO_UNAVAILABLE = "VIDEO_UNAVAILABLE"
ERROR_VIDEO_REQUIRES_AUTH = "VIDEO_REQUIRES_AUTH"
ERROR_AGE_RESTRICTED = "AGE_RESTRICTED"
ERROR_COUNTRY_BLOCKED = "COUNTRY_BLOCKED"
ERROR_LIVE_STREAM_OFFLINE = "LIVE_STREAM_OFFLINE"
ERROR_NETWORK_ERROR = "NETWORK_ERROR"
ERROR_EXTRACTION_FAILED = "EXTRACTION_FAILED"
ERROR_DOWNLOAD_FAILED = "DOWNLOAD_FAILED"

# Processing errors (video-processor-api specific)
ERROR_VIDEO_DOWNLOAD_FAILED = "VIDEO_DOWNLOAD_FAILED"
ERROR_OPERATION_FAILED = "OPERATION_FAILED"
ERROR_FFMPEG_ERROR = "FFMPEG_ERROR"
ERROR_INVALID_TIME_RANGE = "INVALID_TIME_RANGE"
ERROR_INVALID_TEMPLATE = "INVALID_TEMPLATE"

# Generic errors
ERROR_UNKNOWN = "UNKNOWN_ERROR"
ERROR_INTERNAL_SERVER = "INTERNAL_SERVER_ERROR"
ERROR_NO_FILE_DOWNLOADED = "NO_FILE_DOWNLOADED"


# ============================================
# ERROR RESPONSE HELPERS (Unified Structure)
# ============================================

def create_simple_error(error_message: str, error_code: str) -> Dict[str, Any]:
    """
    Creates Level 1 simple error response for validation, auth, and not found errors.

    Args:
        error_message: Human-readable error description
        error_code: Error code constant (e.g., ERROR_INVALID_API_KEY)

    Returns:
        Dictionary with standardized error structure

    Example:
        >>> create_simple_error("Invalid API key", ERROR_INVALID_API_KEY)
        {
            "status": "error",
            "error": "Invalid API key",
            "error_code": "INVALID_API_KEY"
        }
    """
    return {
        "status": "error",
        "error": error_message,
        "error_code": error_code
    }


def create_task_error(
    task_id: str,
    error_message: str,
    error_code: str,
    operation: str = "process_task",
    metadata_url: Optional[str] = None,
    client_meta: Optional[Dict[str, Any]] = None,
    raw_error: Optional[str] = None,
    user_action: Optional[str] = None,
    error_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates Level 2 task processing error response for failed operations.

    Args:
        task_id: UUID of the failed task
        error_message: Human-readable error description
        error_code: Error code constant
        operation: Operation that failed (e.g., "download_video", "make_short")
        metadata_url: Optional URL to full metadata.json
        client_meta: Optional client metadata to pass through
        raw_error: Optional raw exception message (truncated to 1000 chars)
        user_action: Optional suggested action for the user
        error_type: Optional legacy error type for backward compatibility

    Returns:
        Dictionary with standardized task error structure

    Example:
        >>> create_task_error(
        ...     task_id="abc-123",
        ...     error_message="Video is unavailable",
        ...     error_code=ERROR_VIDEO_UNAVAILABLE,
        ...     operation="download_video",
        ...     user_action="Check if video exists"
        ... )
        {
            "task_id": "abc-123",
            "status": "error",
            "error": "Video is unavailable",
            "error_code": "VIDEO_UNAVAILABLE",
            "error_details": {
                "operation": "download_video",
                "failed_at": "2025-11-26T12:00:00"
            },
            "user_action": "Check if video exists"
        }
    """
    response = {
        "task_id": task_id,
        "status": "error",
        "error": error_message,
        "error_code": error_code,
        "error_details": {
            "operation": operation,
            "failed_at": datetime.now().isoformat()
        }
    }

    if raw_error:
        response["error_details"]["raw_error"] = raw_error[:1000]

    if user_action:
        response["user_action"] = user_action

    if error_type:
        response["error_type"] = error_type

    if metadata_url:
        response["metadata_url"] = metadata_url

    if client_meta is not None:
        response["client_meta"] = client_meta

    return response


def create_internal_error(exception_message: str) -> Dict[str, Any]:
    """
    Creates Level 3 internal server error response for unexpected exceptions.

    Args:
        exception_message: Exception message to include in details

    Returns:
        Dictionary with standardized internal error structure

    Example:
        >>> create_internal_error("Redis connection failed")
        {
            "status": "error",
            "error": "Internal server error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "error_details": {
                "message": "Redis connection failed",
                "timestamp": "2025-11-26T12:00:00"
            }
        }
    """
    return {
        "status": "error",
        "error": "Internal server error occurred",
        "error_code": ERROR_INTERNAL_SERVER,
        "error_details": {
            "message": str(exception_message)[:500],
            "timestamp": datetime.now().isoformat()
        }
    }


# ============================================
# ERROR TYPE MAPPING (YouTube Downloader)
# ============================================

def map_youtube_error_type_to_code(error_type: str) -> str:
    """
    Maps legacy youtube error types to unified error codes.

    This function provides backward compatibility by mapping old error_type
    values (from classify_youtube_error) to new unified error codes.

    Args:
        error_type: Legacy error type string

    Returns:
        Unified error code constant

    Example:
        >>> map_youtube_error_type_to_code("private_video")
        "VIDEO_UNAVAILABLE"
    """
    error_code_map = {
        # Recoverable errors
        "network_or_server_error": ERROR_NETWORK_ERROR,
        "authentication_required": ERROR_VIDEO_REQUIRES_AUTH,
        "network_error": ERROR_NETWORK_ERROR,
        "rate_limit": ERROR_NETWORK_ERROR,
        # Non-recoverable errors
        "private_video": ERROR_VIDEO_UNAVAILABLE,
        "unavailable": ERROR_VIDEO_UNAVAILABLE,
        "deleted": ERROR_VIDEO_UNAVAILABLE,
        "region_blocked": ERROR_COUNTRY_BLOCKED,
        "age_restricted": ERROR_AGE_RESTRICTED,
        "copyright_claim": ERROR_VIDEO_UNAVAILABLE,
        "not_found": ERROR_VIDEO_UNAVAILABLE,
        "unknown": ERROR_UNKNOWN
    }
    return error_code_map.get(error_type, ERROR_UNKNOWN)


# ============================================
# UTILITY FUNCTIONS
# ============================================

def is_youtube_url(url: str) -> bool:
    """
    Validates if URL is from YouTube.

    Args:
        url: URL string to validate

    Returns:
        True if URL is from youtube.com or youtu.be

    Example:
        >>> is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        True
        >>> is_youtube_url("https://vimeo.com/12345")
        False
    """
    if not isinstance(url, str):
        return False
    url_lower = url.lower()
    return 'youtube.com' in url_lower or 'youtu.be' in url_lower


def format_ttl_human(hours: int) -> str:
    """
    Formats TTL hours into human-readable string.

    Args:
        hours: Number of hours

    Returns:
        Human-readable string (e.g., "2 days", "3 days 6h", "12h")

    Example:
        >>> format_ttl_human(24)
        "1 day"
        >>> format_ttl_human(72)
        "3 days"
        >>> format_ttl_human(30)
        "1 day 6h"
    """
    if hours >= 24:
        days = hours // 24
        remaining_hours = hours % 24
        if remaining_hours == 0:
            return f"{days} day{'s' if days != 1 else ''}"
        else:
            return f"{days} day{'s' if days != 1 else ''} {remaining_hours}h"
    else:
        return f"{hours}h"


# ============================================
# VERSION INFO
# ============================================

API_COMMONS_VERSION = "1.2.0"
API_COMMONS_DATE = "2025-11-26"

__all__ = [
    # Error codes - Authentication
    "ERROR_MISSING_AUTH_TOKEN",
    "ERROR_INVALID_API_KEY",
    # Error codes - Validation
    "ERROR_MISSING_REQUIRED_FIELD",
    "ERROR_INVALID_JSON",
    "ERROR_INVALID_URL",
    "ERROR_INVALID_WEBHOOK_URL",
    "ERROR_INVALID_WEBHOOK_HEADERS",
    "ERROR_INVALID_CLIENT_META",
    "ERROR_INVALID_OPERATION",
    # Error codes - Tasks
    "ERROR_TASK_NOT_FOUND",
    "ERROR_FILE_NOT_FOUND",
    "ERROR_INVALID_PATH",
    # Error codes - Download (YouTube)
    "ERROR_VIDEO_UNAVAILABLE",
    "ERROR_VIDEO_REQUIRES_AUTH",
    "ERROR_AGE_RESTRICTED",
    "ERROR_COUNTRY_BLOCKED",
    "ERROR_LIVE_STREAM_OFFLINE",
    "ERROR_NETWORK_ERROR",
    "ERROR_EXTRACTION_FAILED",
    "ERROR_DOWNLOAD_FAILED",
    # Error codes - Processing (Video)
    "ERROR_VIDEO_DOWNLOAD_FAILED",
    "ERROR_OPERATION_FAILED",
    "ERROR_FFMPEG_ERROR",
    "ERROR_INVALID_TIME_RANGE",
    "ERROR_INVALID_TEMPLATE",
    # Error codes - Generic
    "ERROR_UNKNOWN",
    "ERROR_INTERNAL_SERVER",
    "ERROR_NO_FILE_DOWNLOADED",
    # Error response functions
    "create_simple_error",
    "create_task_error",
    "create_internal_error",
    # Utility functions
    "map_youtube_error_type_to_code",
    "is_youtube_url",
    "format_ttl_human",
    # Version info
    "API_COMMONS_VERSION",
    "API_COMMONS_DATE"
]
