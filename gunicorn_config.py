"""Gunicorn configuration for unified logging format."""
import logging


class CustomFormatter(logging.Formatter):
    """Custom formatter matching application log format."""
    
    def format(self, record):
        # Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
        return f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] [{record.levelname}] {record.getMessage()}"


def on_starting(server):
    """Configure logging when gunicorn starts."""
    # Disable access log entirely
    server.log.access_log.disabled = True
    
    # Configure error logger
    for handler in server.log.error_log.handlers:
        handler.setFormatter(CustomFormatter())


# Logging
accesslog = None  # Disable access log
errorlog = "-"    # Error log to stdout
loglevel = "info"
