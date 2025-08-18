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
# Global variable to hold the engine instance and a lock for thread-safe access
current_engine: Final[TidyCoreEngine | None] = None
engine_lock = threading.Lock()
shutting_down = False  # FIXED: Add shutdown flag

def start_engine_thread(logger) -> TidyCoreEngine:
    """Initializes and runs the TidyCoreEngine, returning the instance."""
    global current_engine
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        logger.critical("Configuration error: %s", exc)
        raise ConfigError from exc

    engine = TidyCoreEngine(config)
    with engine_lock:
        current_engine = engine # Store the instance globally
    
    engine_thread = threading.Thread(
        target=engine.run,
        daemon=False,  # FIXED: Non-daemon thread so it continues running
        name="TidyCoreEngineThread",
    )
    engine_thread.start()
    
    # FIXED: Give engine thread time to initialize before returning
    import time
    time.sleep(0.5)
    
    return engine


def run_gui_application(logger, engine) -> int:
    """Initializes and runs the main GUI application."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = TidyCoreGUI(engine, app)
    # REMOVED: Config change signal connections that caused engine restart
    # The engine will continue running without restart even if config changes
    window.show()
    return app.exec()


def restart_engine_flow(logger):
    """Stops the current engine and starts a new one in a thread-safe manner."""
    global shutting_down
    
    # FIXED: Don't restart engine if application is shutting down
    if shutting_down:
        logger.info("Application is shutting down - skipping engine restart")
        return
        
    logger.info("Restarting engine due to configuration change...")
    
    global current_engine
    
    with engine_lock:
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
        # REMOVED: Connect the restart signal that was causing engine stops
        # signals.restart_engine.connect(lambda: restart_engine_flow(logger))
        gui_exit_code = run_gui_application(logger, engine)
    except Exception as exc:
        logger.critical("An unexpected error occurred in the GUI: %s", exc, exc_info=True)
        return EXIT_UNKNOWN_ERROR

    # FIXED: Keep the process alive even after GUI closes
    # The engine should continue running in background for file monitoring
    logger.info("GUI closed - engine continues running in background.")
    
    try:
        # Keep the main thread alive to prevent process from exiting
        # The engine will continue monitoring files in its daemon=False thread
        import time
        while current_engine and current_engine.is_running:
            time.sleep(1)  # Check every second if engine is still running
        logger.info("Engine stopped - application will now exit.")
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt - stopping engine...")
        if current_engine:
            current_engine.stop()
    
    return gui_exit_code


# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(main() or EXIT_SUCCESS)