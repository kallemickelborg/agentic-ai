import logging


def setup_logging():
    """Configure logging for the application."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

    return logging.getLogger(__name__)


# Create and export logger instance
logger = setup_logging()

__all__ = ["logger", "setup_logging"]
