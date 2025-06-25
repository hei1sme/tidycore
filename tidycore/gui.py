# tidycore/gui.py
import sys
import os
import logging # Added for logging in the GUI class
import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QFrame, QLabel, QStackedWidget, QGroupBox, QTextEdit,
    QButtonGroup, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction

from tidycore.signals import signals
# from tidycore.settings_page import SettingsPage # We will re-add this later

# STYLESHEET remains the same as the last version.
STYLESHEET = """
/* ---- Main Window ---- */
#MainWindow {
    background-color: #1a1b26; /* Very dark navy background */
}
/* ... (rest of the stylesheet is unchanged) ... */
#Sidebar {
    background-color: #24283b; /* Slightly lighter sidebar */
    border-right: 1px solid #3b3f51;
}
#Sidebar QPushButton {
    background-color: transparent;
    border: none;
    color: #a9b1d6;
    text-align: left;
    padding: 10px;
    border-radius: 8px; /* Slightly more rounded */
    font-size: 14px;
}
#Sidebar QPushButton:hover {
    background-color: #414868;
}
#Sidebar QPushButton:checked {
    background-color: #7aa2f7; /* Bright blue for active button */
    color: #ffffff;
    font-weight: bold;
}
#ContentArea {
    padding: 10px;
}
QGroupBox {
    background-color: #24283b;
    border-radius: 8px;
    border: 1px solid #3b3f51;
    margin-top: 10px;
    padding-top: 10px;
    font-size: 14px;
    font-weight: bold;
    color: #c0c5ea;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 10px;
}
QLabel {
    color: #a9b1d6;
    font-size: 13px;
    font-weight: normal;
}
QLabel#StatusLabel {
    font-size: 20px;
    font-weight: bold;
    color: #9ece6a; /* Green for active */
}
QLabel#StatusLabel[paused="true"] {
    color: #f7768e; /* Red/Pink for paused */
}
QTextEdit {
    background-color: #1a1b26;
    border: 1px solid #3b3f51;
    border-radius: 5px;
    color: #a9b1d6;
}
"""


class TidyCoreGUI(QMainWindow):
    """The main GUI window for TidyCore, featuring a sidebar and content area."""

    def __init__(self, engine, app: QApplication):
        super().__init__()
        self.engine = engine
        self.app = app
        self.logger = logging.getLogger("TidyCore") # Added logger instance

        self.setWindowTitle("TidyCore")
        self.setMinimumSize(900, 650)
        self.setObjectName("MainWindow")
        self.setStyleSheet(STYLESHEET)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        sidebar = self._create_sidebar()
        content_area = self._create_content_area()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area, 1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        self._create_tray_icon()
        self._connect_signals()
        QTimer.singleShot(100, self.engine.request_status)


    def _create_sidebar(self) -> QWidget:
        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("Sidebar")
        sidebar_widget.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)

        title_label = QLabel("TidyCore")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff; margin-bottom: 20px; padding-left: 5px;")
        
        self.dashboard_button = QPushButton("  Dashboard")
        self.dashboard_button.setIcon(qta.icon("fa5s.home"))
        self.dashboard_button.setCheckable(True)
        
        self.settings_button = QPushButton("  Settings")
        self.settings_button.setIcon(qta.icon("fa5s.cog"))
        self.settings_button.setCheckable(True)
        
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        self.nav_button_group.addButton(self.dashboard_button)
        self.nav_button_group.addButton(self.settings_button)
        
        self.dashboard_button.setChecked(True)

        sidebar_layout.addWidget(title_label)
        sidebar_layout.addWidget(self.dashboard_button)
        sidebar_layout.addWidget(self.settings_button)

        self.dashboard_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        
        return sidebar_widget


    def _create_content_area(self) -> QWidget:
        content_widget = QWidget()
        content_widget.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_widget)
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        self.dashboard_page = self._create_dashboard_page()
        self.settings_page = self._create_settings_page()
        
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.settings_page)
        
        return content_widget


    def _create_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        
        top_row_layout = QHBoxLayout()
        top_row_layout.addWidget(self._create_status_box())
        top_row_layout.addWidget(self._create_statistics_box())
        
        activity_feed_box = self._create_activity_feed_box()
        
        layout.addLayout(top_row_layout)
        layout.addWidget(activity_feed_box, 1)
        
        return page


    def _create_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("The full Settings page will be loaded here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 16px;")
        layout.addWidget(label)
        return page


    def _create_status_box(self) -> QGroupBox:
        box = QGroupBox("Status")
        layout = QVBoxLayout(box)
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        return box


    def _create_statistics_box(self) -> QGroupBox:
        box = QGroupBox("Statistics")
        layout = QVBoxLayout(box)
        self.stats_label = QLabel("Files Today: 0\nTotal Organized: 0")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)
        return box


    def _create_activity_feed_box(self) -> QGroupBox:
        box = QGroupBox("Live Activity Feed")
        layout = QVBoxLayout(box)
        self.activity_feed = QTextEdit()
        self.activity_feed.setReadOnly(True)
        layout.addWidget(self.activity_feed)
        return box


    def _connect_signals(self):
        signals.log_message.connect(self.add_log_message)
        signals.update_stats.connect(self.update_statistics)
        signals.status_changed.connect(self.update_status)


    def add_log_message(self, message: str):
        self.activity_feed.insertPlainText(f"{message}\n")

    def update_statistics(self, today_count: int, total_count: int):
        self.stats_label.setText(f"Files Today: {today_count}\nTotal Organized: {total_count}")

    def update_status(self, is_running: bool):
        if is_running:
            self.status_label.setText("Active")
            self.status_label.setProperty("paused", False)
        else:
            self.status_label.setText("Paused")
            self.status_label.setProperty("paused", True)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _create_tray_icon(self):
        """Creates the system tray icon and its context menu."""
        icon_path = os.path.join(os.getcwd(), "icon.png")
        
        if not os.path.exists(icon_path):
            self.logger.warning(f"Icon file 'icon.png' not found in the project directory.")
            self.logger.warning("Using a default system icon as a fallback. Please add 'icon.png' for a custom icon.")
            # --- FIX: Use a more reliable standard icon ---
            # SP_DesktopIcon is a very safe fallback that should exist on all platforms.
            icon = self.style().standardIcon(getattr(self.style(), 'SP_DesktopIcon'))
        else:
            icon = QIcon(icon_path)
            
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("TidyCore")
        
        menu = QMenu()
        show_action = QAction("Show Dashboard", self)
        quit_action = QAction("Quit TidyCore", self)

        show_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(self.app.quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
    
    def show_window(self):
        """Brings the main window to the front."""
        self.show()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        """Override the window's close event."""
        if self.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "TidyCore",
                "TidyCore is still running in the background.",
                QSystemTrayIcon.Information,
                2000
            )