import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from api.config.config import settings

def setup_logging():
    """
    Configures the root logger with StreamHandler and TimedRotatingFileHandler.
    """
    logger = logging.getLogger()
    
    level = logging.DEBUG if settings.debug else logging.INFO
    logger.setLevel(level)

    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(level)
    c_handler.setFormatter(log_format)

    log_file = settings.log_file
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    f_handler = TimedRotatingFileHandler(
        log_file, 
        when="midnight",
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    f_handler.setLevel(level)
    f_handler.setFormatter(log_format)

    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
