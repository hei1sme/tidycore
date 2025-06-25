# tidycore/signals.py
from PySide6.QtCore import QObject, Signal

class TidyCoreSignals(QObject):
    log_message = Signal(str)
    update_stats = Signal(int, int)
    status_changed = Signal(bool)
    restart_engine = Signal()
    folder_decision_made = Signal(str, str, str)
    file_organized = Signal(str)
    config_changed = Signal()

signals = TidyCoreSignals()