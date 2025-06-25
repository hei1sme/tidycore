# main.py
import sys
import threading
from typing import Final

from PySide6.QtWidgets import QApplication
from tidycore.gui import TidyCoreGUI
from tidycore.logger import setup_logger
from tidycore.engine import TidyCoreEngine
from tidycore.config_manager import load_config

# ────────────────────────────────────────────────────────────
# Define application exit codes for clear error handling in CI/CD and shell scripts.
EXIT_CONFIG_ERROR: Final[int] = 1
EXIT_UNKNOWN_ERROR: Final[int] = 2
EXIT_SUCCESS: Final[int] = 0


class ConfigError(Exception):
    """Custom exception raised for configuration-related issues."""
    pass


# ────────────────────────────────────────────────────────────
def start_engine_thread(logger):
    """
    Initializes and runs the TidyCoreEngine in a background thread.

    This function is designed to be the target of a thread, keeping the
    engine's blocking `run()` method off the main GUI thread.
    This ensures the UI remains responsive.
    """
    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as exc:
        logger.critical("Configuration error: %s", exc)
        # This custom exception allows the main thread to catch specific startup failures.
        raise ConfigError from exc

    engine = TidyCoreEngine(config)
    # The engine's own logger will announce its start and other activities.
    engine.run()  # This is a blocking call, but it's safe inside its own thread.


# ────────────────────────────────────────────────────────────
def run_gui_application(logger) -> int:
    """
    Initializes and runs the main GUI application.

    This function is responsible for the main event loop and returns
    the application's exit code upon termination.
    """
    app = QApplication(sys.argv)
    window = TidyCoreGUI()
    window.show()
    return app.exec()


# ────────────────────────────────────────────────────────────
def main() -> int:
    """The main entry point for the TidyCore application."""
    logger = setup_logger()
    logger.info("TidyCore application starting...")

    # Set up the engine to run in a background daemon thread.
    # A daemon thread will exit automatically when the main application exits.
    engine_thread = threading.Thread(
        target=start_engine_thread,
        args=(logger,),
        daemon=True,
        name="TidyCoreEngineThread",
    )

    try:
        # Start the background thread.
        engine_thread.start()
    except ConfigError:
        # The engine thread failed to start due to a config issue.
        # The logger has already recorded the details. Exit with a specific code.
        return EXIT_CONFIG_ERROR
    except Exception as exc:
        # Catch any other unexpected errors during thread startup.
        logger.critical("Unexpected error while starting engine thread: %s", exc, exc_info=True)
        return EXIT_UNKNOWN_ERROR

    # The engine is now running (or attempting to run) in the background.
    # Now, start the GUI, which will block the main thread until the user closes it.
    try:
        gui_exit_code = run_gui_application(logger)
    except Exception as exc:
        logger.critical("An unexpected error occurred in the GUI: %s", exc, exc_info=True)
        return EXIT_UNKNOWN_ERROR

    # The GUI has been closed by the user.
    logger.info("Application shutting down gracefully.")
    return gui_exit_code


# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Call main and exit the script with the appropriate code.
    # The 'or EXIT_SUCCESS' handles cases where main() might return None.
    sys.exit(main() or EXIT_SUCCESS)