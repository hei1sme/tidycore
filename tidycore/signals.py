# tidycore/signals.py
from PySide6.QtCore import QObject, Signal

class TidyCoreSignals(QObject):
    """
    Defines custom signals that the TidyCoreEngine can emit.
    
    This allows the backend engine (running in a separate thread) to safely 
    communicate with the frontend GUI.
    """
    # Signal emitted when a message should be logged to the GUI's activity feed.
    # Argument: str (the message)
    log_message = Signal(str)
    
    # Signal emitted to update the statistics on the GUI.
    # Arguments: int (files today), int (total files)
    update_stats = Signal(int, int)
    
    # Signal emitted to update the engine's status on the GUI.
    # Argument: bool (True if running, False if paused)
    status_changed = Signal(bool)
    
    # Signal emitted when settings have been changed and the engine needs a restart.
    restart_engine = Signal()
    
    # Emitted when a folder is moved, carrying all necessary info for the UI.
    # Arguments:
    #   str: Original path of the folder before it was moved.
    #   str: The new, final path of the folder after the move.
    #   str: The category it was moved into (e.g., "Images").
    folder_decision_made = Signal(str, str, str)

    # --- NEW SIGNAL ---
    # Emitted when category statistics change, for the chart.
    # Argument: dict (e.g., {"Images": 10, "Documents": 5})
    chart_data_updated = Signal(dict)

# Create a single, global instance of the signals object that can be imported
# by both the engine and the GUI to ensure they are connected to the same signals.
signals = TidyCoreSignals()