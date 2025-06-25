# tidycore/logger.py
import logging
import sys

def setup_logger() -> logging.Logger:
    """Sets up a standardized logger for the application."""
    logger = logging.getLogger("TidyCore")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    # --- FIX: Explicitly set encoding to 'utf-8' ---
    # Create a handler for console output (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    
    # Create a handler for writing to a log file
    file_handler = logging.FileHandler("tidycore.log", mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    return logger