import logging

from rich.logging import RichHandler


def set_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Disable propagation to higher-level (root) logger
    logger.propagate = False

    # Clear all handlers
    logger.handlers = []

    handler = RichHandler(rich_tracebacks=True)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
