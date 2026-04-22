import sys
import os
import logging
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    This intercepts standard Python logging calls (like FastAPI's default logs)
    and routes them into the Loguru engine.
    """
    def emit(self, record):

        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno


        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logger():

    logger.remove()

    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    if not os.path.exists("logs"):
        os.makedirs("logs")

    logger.add(
        "logs/system_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="14 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        backtrace=True,
        diagnose=True
    )

    # Tell Uvicorn and FastAPI to use our InterceptHandler instead of their own
    logging.getLogger("uvicorn").handlers        = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers  = [InterceptHandler()]
    logging.getLogger("fastapi").handlers        = [InterceptHandler()]

    # Prevent Uvicorn from spamming duplicate logs directly to the console
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate  = False

    return logger

# Export an initialized instance
sys_logger = setup_logger()