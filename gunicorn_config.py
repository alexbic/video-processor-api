"""Gunicorn configuration for unified logging format."""
import logging
from gunicorn.glogging import Logger


class CustomFormatter(logging.Formatter):
    """Custom formatter matching application log format."""
    
    def format(self, record):
        # Format: [YYYY-MM-DD HH:MM:SS] [LEVEL] message
        return f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] [{record.levelname}] {record.getMessage()}"


class CustomLogger(Logger):
    """Custom logger class that applies formatting from the start."""
    
    def setup(self, cfg):
        super().setup(cfg)
        # Apply custom formatter to all handlers immediately
        formatter = CustomFormatter()
        for handler in self.error_log.handlers:
            handler.setFormatter(formatter)
        # Disable access log
        self.access_log.disabled = True


# Use custom logger class
logger_class = "gunicorn_config.CustomLogger"

# Logging
accesslog = None  # Disable access log
errorlog = "-"    # Error log to stdout
loglevel = "info"
