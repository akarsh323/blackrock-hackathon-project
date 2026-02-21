import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = logging.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    level: str = "INFO",
) -> None:
    """
    Configure Loguru sinks and route only Uvicorn loggers into Loguru by default.

    - If you want *all* stdlib loggers to go through Loguru, set only_uvicorn=False.
    - Pass `log_config=None` to uvicorn.run(...) to avoid duplicate handlers.
    """

    intercept_handler = InterceptHandler()

    logging.basicConfig(handlers=[intercept_handler], level=level)

    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("uvicorn"):
            logging.getLogger(logger_name).handlers = []

    logging.getLogger("uvicorn").handlers = [intercept_handler]
    logging.getLogger("uvicorn.access").handlers = [intercept_handler]

    logger.remove()
    logger.add(sys.stdout, level="INFO")
