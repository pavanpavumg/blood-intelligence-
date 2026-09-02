import logging
import sys
from app.core.config import settings

def setup_logging() -> logging.Logger:
    """
    Configures and returns structured system logger.
    """
    logger = logging.getLogger(settings.PROJECT_NAME)
    
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger: logging.Logger = setup_logging()
