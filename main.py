# main.py
import sys
from tidycore.engine import TidyCoreEngine
from tidycore.config_manager import load_config
from tidycore.logger import setup_logger

def main():
    """The main entry point for the TidyCore application."""
    logger = setup_logger()
    logger.info("Application starting up...")

    try:
        config = load_config()
        engine = TidyCoreEngine(config)
        engine.run()
    except (FileNotFoundError, ValueError) as e:
        logger.critical(f"A critical error occurred: {e}")
        logger.critical("TidyCore cannot start. Please check your configuration.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()