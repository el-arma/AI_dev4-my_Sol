import logging
import time
from pathlib import Path


class CustomFormatter(logging.Formatter):
    def format(self, record):
        record.ts = int(time.time() * 1000)
        return super().format(record)


def setup_logger() -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = CustomFormatter(
        "%(asctime)s | ts=%(ts)s | %(levelname)s | %(message)s"
    )

    handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger