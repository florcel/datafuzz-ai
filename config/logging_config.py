"""Logging configuration for Datafuzz application.

Provides structured logging setup with appropriate levels for different modules.
"""
import logging.config
import sys
from pathlib import Path

# Determine if we're in a terminal (for colored output)
SUPPORTS_COLOR = sys.stdout.isatty()


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/datafuzz.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {  # Root logger
            "level": "DEBUG",
            "handlers": ["console", "file"],
        },
        "httpx": {
            "level": "WARNING",  # Reduce noise from httpx
        },
        "asyncio": {
            "level": "WARNING",  # Reduce noise from asyncio
        },
    },
}


def configure_logging():
    """Initialize logging configuration.
    
    Sets up console and file handlers with appropriate formatters.
    Creates logs directory if it doesn't exist.
    """
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Apply configuration
    logging.config.dictConfig(LOG_CONFIG)
    
    logger = logging.getLogger(__name__)
    logger.debug("Logging configured successfully")
