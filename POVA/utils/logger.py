"""Privacy-conscious rotating application logging."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging() -> logging.Logger:
    log_directory = Path(__file__).resolve().parents[1] / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("pova")
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_directory / "pova.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
