import logging
import sys

try:
    from app.core.config import get_settings
    settings = get_settings()
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
except Exception as e:
    print(f"[logging] Config load failed: {e}, using INFO")
    settings = None
    log_level = logging.INFO


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    return logger


logger = setup_logging()
