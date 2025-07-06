# main.py
import sys
import threading
import time
from typing import Final

from PySide6.QtWidgets import QApplication
from src.tidycore.gui import TidyCoreGUI
from src.tidycore.logger import setup_logger
from src.tidycore.engine import TidyCoreEngine
from src.tidycore.config_manager import load_config
from src.tidycore.signals import signals

# ────────────────────────────────────────────────────────────
# Define application exit codes for clear error handling in CI/CD and shell scripts.
EXIT_CONFIG_ERROR: Final[int] = 1
EXIT_UNKNOWN_ERROR: Final[int] = 2
EXIT_SUCCESS: Final[int] = 0


class ConfigError(Exception):
    """Custom exception raised for configuration-related issues."""
    pass


# ────────────────────────────────────────────────────────────
# Global variable to hold the engine instance
current_engine: Final[TidyCoreEngine | None] = None

def start_engine_thread(logger) -> TidyCoreEngine:
    """Initializes and runs the TidyCoreEngine, returning the instance."""
    global current_engine
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        logger.critical("Configuration error: %s", exc)
        raise ConfigError from exc

    engine = TidyCoreEngine(config)
    current_engine = engine # Store the instance globally
    
    engine_thread = threading.Thread(
        target=engine.run,
        daemon=True,
        name="TidyCoreEngineThread",
    )
    engine_thread.start()
    return engine


def run_gui_application(logger, engine) -> int:
    """Initializes and runs the main GUI application."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = TidyCoreGUI(engine, app)
    signals.config_changed.connect(lambda: restart_engine_flow(logger))
    window.show()
    return app.exec()


def restart_engine_flow(logger):
    """Stops the current engine and starts a new one."""
    logger.info("Restarting engine due to configuration change...")
    
    global current_engine
    if current_engine:
        current_engine.stop()
    
    time.sleep(1) 
    
    try:
        new_engine = start_engine_thread(logger)
        for widget in QApplication.instance().topLevelWidgets():
            if isinstance(widget, TidyCoreGUI):
                widget.engine = new_engine
                # Let the GUI know it can request the new status
                new_engine.request_status()
                break
    except ConfigError:
        logger.critical("Failed to restart engine with new configuration.")
        signals.log_message.emit("[ERROR] Failed to restart engine. Please check config.json.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred during engine restart: {e}")
        signals.log_message.emit(f"[ERROR] An unexpected error occurred during restart: {e}")


def main() -> int:
    """The main entry point for the TidyCore application."""
    logger = setup_logger()
    logger.info("TidyCore application starting...")

    try:
        engine = start_engine_thread(logger)
    except ConfigError:
        return EXIT_CONFIG_ERROR
    except Exception as exc:
        logger.critical("Unexpected error while starting engine thread: %s", exc, exc_info=True)
        return EXIT_UNKNOWN_ERROR

    try:
        # Connect the restart signal here, before starting the GUI event loop
        signals.restart_engine.connect(lambda: restart_engine_flow(logger))
        gui_exit_code = run_gui_application(logger, engine)
    except Exception as exc:
        logger.critical("An unexpected error occurred in the GUI: %s", exc, exc_info=True)
        return EXIT_UNKNOWN_ERROR

    if current_engine:
        current_engine.stop()
    logger.info("Application shutting down gracefully.")
    return gui_exit_code


# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(main() or EXIT_SUCCESS)