# tidycore/utils.py
import sys
import os

def get_absolute_path(relative_path: str) -> str:
    """
    Gets the absolute path to a resource, works for both development (script)
    and production (packaged with PyInstaller).
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # This is the base path of the bundled application.
        base_path = sys._MEIPASS
    except Exception:
        # _MEIPASS is not set, so we are running in a normal Python environment.
        # The base path is the directory of the main script.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)