import logging
import logging.config
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGGING_LEVEL = logging.DEBUG

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] [%(threadName)s] [in %(pathname)s:[%(module)s:%(lineno)d] [%(levelname)s]: %(message)s"
        },
    },
    "handlers": {
        "file": {
            "level": LOGGING_LEVEL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logg.txt"),
            "formatter": "simple",
        },
        "console": {
            "level": LOGGING_LEVEL,
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "simple",
        },
        "null": {
            "level": "DEBUG",
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "elixir": {
            "handlers": ["console"],
            "level": LOGGING_LEVEL,
            "propagate": True,
        },
        "apps.*": {
            "handlers": ["console", "file"],
            "level": LOGGING_LEVEL,
            "propagate": True,
        },
    },
}
