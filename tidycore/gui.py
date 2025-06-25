# tidycore/gui.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QGroupBox, QTextEdit, QSystemTrayIcon, QMenu, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction

# --- Import project modules ---
from tidycore.signals import signals
from tidycore.settings_window import SettingsWindow
from tidycore.config_manager import ConfigManager

# --- Modern Stylesheet (QSS) ---
# This is like CSS for our Qt application. We define the visual style here.
MODERN_STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e; /* Dark blue-purple background */
}

QGroupBox {
    background-color: #27293d; /* Slightly lighter background for boxes */
    border-radius: 10px;
    border: 1px solid #3a3c5a;
    margin-top: 10px;
    font-size: 14px;
    font-weight: bold;
    color: #c0c5ea; /* Lavender text color for titles */
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    left: 10px;
}

QLabel {
    color: #c0c5ea;
    font-size: 13px;
    font-weight: normal;
}

QLabel#StatusLabel {
    font-size: 24px;
    font-weight: bold;
    color: #50fa7b; /* Bright green for active status */
}

QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff79c6, stop:1 #bd93f9); /* Pink to purple gradient */
    color: white;
    border-radius: 5px;
    padding: 8px 15px;
    font-size: 13px;
    font-weight: bold;
    border: none;
}

QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff92d0, stop:1 #c9a3fa); /* Lighter on hover */
}

QPushButton:pressed {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e06ab0, stop:1 #ad82e0); /* Darker when pressed */
}
"""

class TidyCoreGUI(QMainWindow):
    """The main GUI window for the TidyCore application."""

    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        # --- NEW: Instantiate the config manager ---
        self.config_manager = ConfigManager()

        self.setWindowTitle("TidyCore Dashboard")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(MODERN_STYLESHEET)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.grid_layout = QGridLayout(central_widget)

        self._create_status_box()
        self._create_chart_box()
        self._create_activity_feed_box()
        self._create_folder_decisions_box()
        self._create_statistics_box()
        self._create_settings_box()
        
        self._create_tray_icon()
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect engine signals to the GUI's update methods."""
        signals.log_message.connect(self.add_log_message)
        signals.update_stats.connect(self.update_statistics)
        signals.status_changed.connect(self.update_status)
    
    def add_log_message(self, message: str):
        """Adds a message to the beginning of the activity feed."""
        self.activity_feed.insertPlainText(f"{message}\n")

    def update_statistics(self, today_count: int, total_count: int):
        """Updates the statistics labels."""
        self.stats_label.setText(f"Files Today: {today_count}\nTotal Organized: {total_count}")

    def update_status(self, is_running: bool):
        """Updates the status label and pause/resume button text."""
        if is_running:
            self.status_label.setText("Actively Watching")
            self.status_label.setStyleSheet("color: #50fa7b;") # Green
            self.pause_button.setText("Pause Watching")
        else:
            self.status_label.setText("Paused")
            self.status_label.setStyleSheet("color: #f1fa8c;") # Yellow
            self.pause_button.setText("Resume Watching")

    def _create_status_box(self) -> None:
        """Creates the main status and quick actions box."""
        box = QGroupBox("Status & Quick Actions")
        layout = QGridLayout(box)

        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pause_button = QPushButton("Pause Watching")
        self.organize_button = QPushButton("Organize Now")
        
        self.pause_button.clicked.connect(self.toggle_pause_resume)

        layout.addWidget(self.status_label, 0, 0, 1, 2)
        layout.addWidget(self.pause_button, 1, 0)
        layout.addWidget(self.organize_button, 1, 1)

        self.grid_layout.addWidget(box, 0, 0, 1, 2)
        
    def toggle_pause_resume(self):
        """Toggles the engine's running state."""
        if self.engine.is_running:
            self.engine.pause()
        else:
            self.engine.resume()
            
    def _create_chart_box(self) -> None:
        """Creates a placeholder for the category breakdown chart."""
        box = QGroupBox("Category Breakdown")
        layout = QGridLayout(box)
        
        placeholder_label = QLabel("Chart will be displayed here.")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(placeholder_label)

        self.grid_layout.addWidget(box, 0, 2, 1, 1)

    def _create_activity_feed_box(self) -> None:
        """Creates the box for the live activity feed."""
        box = QGroupBox("Live Activity Feed")
        layout = QGridLayout(box)

        self.activity_feed = QTextEdit()
        self.activity_feed.setReadOnly(True)
        self.activity_feed.setStyleSheet("background-color: #1e1e2e; border: none;")
        layout.addWidget(self.activity_feed)

        self.grid_layout.addWidget(box, 1, 0, 2, 2)

    def _create_folder_decisions_box(self) -> None:
        """Creates the box for recent folder decisions."""
        box = QGroupBox("Recent Folder Decisions")
        layout = QGridLayout(box)
        
        placeholder_label = QLabel("No recent folder decisions to show.")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(placeholder_label)

        self.grid_layout.addWidget(box, 1, 2, 2, 1)

    def _create_statistics_box(self) -> None:
        """Creates the box for key statistics."""
        box = QGroupBox("Statistics")
        layout = QGridLayout(box)
        
        self.stats_label = QLabel("Files Today: 0\nTotal Organized: 0")
        layout.addWidget(self.stats_label)

        self.grid_layout.addWidget(box, 3, 0, 1, 1)

    def _create_settings_box(self) -> None:
        """Creates the box for settings and logs navigation."""
        box = QGroupBox("Settings & Logs")
        layout = QGridLayout(box)

        settings_button = QPushButton("Settings")
        logs_button = QPushButton("View Full Log")

        # --- NEW: Connect the settings button ---
        settings_button.clicked.connect(self._open_settings_window)
        
        layout.addWidget(settings_button, 0, 0)
        layout.addWidget(logs_button, 0, 1)

        self.grid_layout.addWidget(box, 3, 1, 1, 2)

    # --- NEW: Method to launch the settings window ---
    def _open_settings_window(self):
        """Creates and shows the settings dialog."""
        # Pause the engine while settings are being changed
        was_running = self.engine.is_running
        if was_running:
            self.engine.pause()
        
        dialog = SettingsWindow(self.config_manager, self)
        # The `exec()` call makes the dialog modal (blocks the main window)
        result = dialog.exec()
        
        # The dialog's `accept()` was called, meaning the user clicked "Save"
        if result == QDialog.Accepted:
            signals.log_message.emit("Settings saved. Restarting engine to apply changes...")
            signals.restart_engine.emit()
        else:
            # User clicked "Cancel" or closed the window, so resume if it was running before
            if was_running:
                self.engine.resume()

    def _create_tray_icon(self):
        """Creates the system tray icon and its context menu."""
        # You'll need an icon file, e.g., 'icon.png' in your root directory
        # Using a dummy icon for now, will need to be created.
        if QIcon.hasThemeIcon("document-save"):
            icon = QIcon.fromTheme("document-save")
        else:
            icon = QIcon() # Fallback to a blank icon if none are found.
            
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("TidyCore is running")
        
        menu = QMenu()
        show_action = QAction("Show Dashboard", self)
        quit_action = QAction("Quit TidyCore", self)

        show_action.triggered.connect(self.show)
        quit_action.triggered.connect(QApplication.instance().quit)

        menu.addAction(show_action)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        """Override the close event to hide the window instead of quitting."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "TidyCore",
            "TidyCore is still running in the background. Right-click the tray icon to quit.",
            QSystemTrayIcon.Information,
            2000
        )