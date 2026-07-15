import sys

from loguru import logger


def configure_logging() -> None:
    """Configure a simple global logger."""
    logger.remove()
    logger.add(sys.stdout, level="INFO", colorize=False)


__all__ = ["configure_logging", "logger"]
