# tidycore/gui.py
import sys
import os
import logging
import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QGroupBox, QTextEdit,
    QButtonGroup, QSystemTrayIcon, QMenu, QGridLayout, QScrollArea,
    QGraphicsDropShadowEffect, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction, QColor, QFont

from .signals import signals
from .pie_chart_widget import PieChartWidget
from .folder_decision_widget import FolderDecisionWidget
from .settings_page import SettingsPage
# --- NEW: Import the AboutPage ---
from .about_page import AboutPage
# --- NEW: Import the get_absolute_path function ---
from .utils import get_absolute_path
# --- NEW: Import the database ---
from .database import statistics_db
# --- NEW: Import the updater safely ---
try:
    from .updater import update_manager
except ImportError as e:
    import logging
    logging.getLogger("TidyCore").warning(f"Failed to import update_manager: {e}")
    update_manager = None
from .update_dialog import UpdateDialog, UpdateNotificationWidget
STYLESHEET = """
/* ---- Main Window ---- */
#MainWindow {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #23243a, stop:1 #1a1b26);
    font-family: 'Segoe UI', 'Inter', 'Roboto', Arial, sans-serif;
}
#Sidebar {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #31355a, stop:1 #23243a);
    border-right: 1px solid #3b3f51;
}
#Sidebar #LogoLabel {
    margin-bottom: 22px;
    padding: 12px 0 12px 0;
    text-align: center;
}
#Sidebar QPushButton {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #23243a, stop:1 #31355a);
    border: none;
    color: #a9b1d6;
    text-align: left;
    padding: 18px 28px;
    border-radius: 18px;
    font-size: 18px;
    margin-bottom: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    /* box-shadow: 0 2px 12px 0 rgba(122,162,247,0.10); */
}
#Sidebar QPushButton:hover {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7aa2f7, stop:1 #7dcfff);
    color: #23243a;
    font-weight: bold;
    /* box-shadow: 0 4px 18px 0 rgba(122,162,247,0.18); */
}
#Sidebar QPushButton:checked {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7aa2f7, stop:1 #bb9af7);
    color: #ffffff;
    font-weight: bold;
    /* box-shadow: 0 6px 24px 0 rgba(122,162,247,0.22); */
    border: 1.5px solid #7aa2f7;
}
/* Modern global QPushButton style */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7aa2f7, stop:1 #7dcfff);
    color: #23243a;
    border: none;
    border-radius: 14px;
    font-size: 17px;
    font-weight: 600;
    padding: 12px 28px;
    margin: 8px 0;
    /* box-shadow: 0 2px 12px 0 rgba(122,162,247,0.10); */
}
/* Specific styling for compact buttons */
QPushButton[objectName="pause_resume_button"] {
    font-size: 14px;
    padding: 8px 16px;
    margin: 4px 0;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #bb9af7, stop:1 #7aa2f7);
    color: #fff;
    /* box-shadow: 0 4px 18px 0 rgba(122,162,247,0.18); */
}
QPushButton:pressed {
    background: #414868;
    color: #fff;
}
#ContentArea {
    padding: 28px 28px 18px 28px;
}
QGroupBox {
    background-color: rgba(35,36,58,0.96);
    border-radius: 24px;
    border: 1.5px solid #363a4f;
    margin-top: 26px;
    padding-top: 26px;
    font-size: 18px;
    font-weight: bold;
    color: #c0c5ea;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 20px;
    left: 28px;
    font-size: 20px;
    color: #7aa2f7;
}
QLabel {
    color: #a9b1d6;
    font-size: 17px;
    font-weight: normal;
}
QLabel#StatusLabel {
    font-size: 30px;
    font-weight: bold;
    color: #9ece6a;
    letter-spacing: 1px;
}
QLabel#StatusLabel[paused="true"] {
    color: #f7768e;
}
QTextEdit {
    background-color: #181926;
    border: 1.5px solid #363a4f;
    border-radius: 16px;
    color: #a9b1d6;
    font-size: 16px;
    padding: 16px;
}
"""
"""
}
"""


class TidyCoreGUI(QMainWindow):
    """The main GUI window for TidyCore, featuring a sidebar and content area."""

    def __init__(self, engine, app: QApplication):
        super().__init__()
        self.engine = engine
        self.app = app
        self.logger = logging.getLogger("TidyCore")

        # --- GUI OWNS ALL DISPLAY DATA ---
        self.category_counts = {}
        self.chart_colors = [
            QColor("#7aa2f7"), QColor("#ff79c6"), QColor("#9ece6a"),
            QColor("#e0af68"), QColor("#bb9af7"), QColor("#7dcfff")
        ]
        
        # --- GUI CONTROLS ITS OWN REFRESH ---
        self.chart_update_timer = QTimer(self)
        self.chart_update_timer.setSingleShot(True)
        self.chart_update_timer.setInterval(250) # Refresh 250ms after the last event
        self.chart_update_timer.timeout.connect(self.redraw_dashboard_charts)

        # --- UPDATE NOTIFICATION WIDGET ---
        self.update_notification = None
        
        # Load initial category data from database
        self.category_counts = statistics_db.get_category_stats_today()

        self.setWindowTitle("TidyCore - File Organization Dashboard")
        self.setMinimumSize(1000, 750) # Slightly larger for better spacing
        self.setObjectName("MainWindow")
        
        # Set window icon
        icon_path = get_absolute_path("icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
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
        
        # --- NEW: Check for updates on startup (silent check) ---
        QTimer.singleShot(2000, lambda: update_manager.check_for_updates(silent=True))
        
        # --- NEW: Connect update manager signals ---
        update_manager.checker.update_available.connect(self.show_update_notification)
        update_manager.checker.error_occurred.connect(self._on_update_error)
        
        QTimer.singleShot(100, self.engine.request_status)


    def _create_sidebar(self) -> QWidget:

        sidebar_widget = QWidget()
        sidebar_widget.setObjectName("Sidebar")
        sidebar_widget.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        sidebar_layout.setContentsMargins(16, 18, 16, 18)
        sidebar_layout.setSpacing(8)

        # Logo or avatar at the top
        logo_label = QLabel()
        logo_label.setObjectName("LogoLabel")
        logo_path = get_absolute_path("icon.png")
        if os.path.exists(logo_path):
            logo_label.setPixmap(QIcon(logo_path).pixmap(64, 64))
        else:
            logo_label.setText("🧹")
            logo_label.setStyleSheet("font-size: 40px; text-align: center; color: #7aa2f7;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sidebar_layout.addWidget(logo_label)

        # App name
        title_label = QLabel("TidyCore")
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ffffff; margin-bottom: 18px; padding-left: 0px; letter-spacing: 2px; text-align: center;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        sidebar_layout.addWidget(title_label)

        # Create navigation buttons
        self.dashboard_button = QPushButton("  Dashboard")
        self.dashboard_button.setIcon(qta.icon("fa5s.home"))
        self.dashboard_button.setCheckable(True)

        self.settings_button = QPushButton("  Settings")
        self.settings_button.setIcon(qta.icon("fa5s.cog"))
        self.settings_button.setCheckable(True)

        self.about_button = QPushButton("  About")
        self.about_button.setIcon(qta.icon("fa5s.info-circle"))
        self.about_button.setCheckable(True)

        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        self.nav_button_group.addButton(self.dashboard_button)
        self.nav_button_group.addButton(self.settings_button)
        self.nav_button_group.addButton(self.about_button)

        self.dashboard_button.setChecked(True)

        # Create indicator bars for modern navigation
        self.dashboard_indicator = QWidget()
        self.dashboard_indicator.setFixedSize(4, 40)
        self.dashboard_indicator.setStyleSheet("background: #7aa2f7; border-radius: 2px;")
        
        self.settings_indicator = QWidget()
        self.settings_indicator.setFixedSize(4, 40)
        self.settings_indicator.setStyleSheet("background: #7aa2f7; border-radius: 2px;")
        
        self.about_indicator = QWidget()
        self.about_indicator.setFixedSize(4, 40)
        self.about_indicator.setStyleSheet("background: #7aa2f7; border-radius: 2px;")

        # Create layouts for each navigation row (indicator + button)
        def create_nav_row(indicator, button):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(8)
            row_layout.addWidget(indicator)
            row_layout.addWidget(button, 1)
            return row_widget

        dashboard_row = create_nav_row(self.dashboard_indicator, self.dashboard_button)
        settings_row = create_nav_row(self.settings_indicator, self.settings_button)
        about_row = create_nav_row(self.about_indicator, self.about_button)

        sidebar_layout.addWidget(dashboard_row)
        sidebar_layout.addWidget(settings_row)
        sidebar_layout.addWidget(about_row)
        sidebar_layout.addStretch(1)

        # Update indicators when buttons are toggled
        def update_indicators():
            self.dashboard_indicator.setVisible(self.dashboard_button.isChecked())
            self.settings_indicator.setVisible(self.settings_button.isChecked())
            self.about_indicator.setVisible(self.about_button.isChecked())

        self.dashboard_button.toggled.connect(update_indicators)
        self.settings_button.toggled.connect(update_indicators)
        self.about_button.toggled.connect(update_indicators)
        
        # Initialize indicators
        update_indicators()

        self.dashboard_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.about_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))

        return sidebar_widget


    def _create_content_area(self) -> QWidget:
        """Creates the main content area with a stacked widget for pages."""
        content_widget = QWidget()
        content_widget.setObjectName("ContentArea")
        content_layout = QVBoxLayout(content_widget)
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        self.dashboard_page = self._create_dashboard_page()
        self.settings_page = SettingsPage()
        # --- NEW: Create an instance of the AboutPage ---
        self.about_page = AboutPage()
        
        # Add all pages to the stacked widget in order
        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.about_page) # Add new page
        
        return content_widget


    def _create_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page) # Use a Grid for more control
        
        # Create all the boxes first
        chart_box = self._create_chart_box()
        status_box = self._create_status_box()
        stats_box = self._create_statistics_box()
        activity_feed_box = self._create_activity_feed_box()
        
        folder_decisions_box = self._create_folder_decisions_box()

        # Add them to the grid
        layout.addWidget(chart_box, 0, 0, 2, 1)    # Row 0, Col 0, span 2 rows, 1 col
        layout.addWidget(status_box, 0, 1)         # Row 0, Col 1
        layout.addWidget(stats_box, 1, 1)          # Row 1, Col 1
        
        # Add the two bottom boxes
        layout.addWidget(activity_feed_box, 2, 0)       # Row 2, Col 0
        layout.addWidget(folder_decisions_box, 2, 1)    # Row 2, Col 1

        # Set stretch factors to control sizing with better proportions
        layout.setColumnStretch(0, 3) # Chart column is larger
        layout.setColumnStretch(1, 2) # Right column
        layout.setRowStretch(0, 2)    # Status row 
        layout.setRowStretch(1, 2)    # Stats row 
        layout.setRowStretch(2, 4)    # Activity feed is largest
        
        # Add spacing between grid items
        layout.setSpacing(20)
        layout.setContentsMargins(10, 10, 10, 10)

        return page


    def _add_card_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(60, 70, 120, 110))
        widget.setGraphicsEffect(shadow)

    def _create_chart_box(self) -> QGroupBox:
        box = QGroupBox("Category Breakdown")
        self._add_card_shadow(box)
        layout = QHBoxLayout(box)
        self.chart_widget = PieChartWidget()
        self.legend_layout = QVBoxLayout()
        self.legend_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.legend_layout.setSpacing(10)
        layout.addWidget(self.chart_widget, 2)
        layout.addLayout(self.legend_layout, 1)
        return box


    def _create_status_box(self) -> QGroupBox:
        box = QGroupBox("Status")
        self._add_card_shadow(box)
        layout = QVBoxLayout(box)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)  # Reduced spacing
        layout.setContentsMargins(15, 20, 15, 15)  # Add margins for better fit
        
        # Status icon and text container
        status_container = QWidget()
        status_layout = QVBoxLayout(status_container)
        status_layout.setSpacing(6)  # Reduced spacing
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # Status icon
        self.status_icon = QLabel("🔄")
        self.status_icon.setStyleSheet("font-size: 28px;")  # Slightly smaller
        self.status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status text
        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        status_layout.addWidget(self.status_icon)
        status_layout.addWidget(self.status_label)
        
        # Button with icon - make it more compact
        self.pause_resume_button = QPushButton("⏸️ Pause Watching")
        self.pause_resume_button.setObjectName("pause_resume_button")
        self.pause_resume_button.setMinimumWidth(160)  # Slightly smaller
        self.pause_resume_button.setMinimumHeight(35)  # Smaller height
        self.pause_resume_button.setMaximumHeight(40)  # Limit max height
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        
        layout.addWidget(status_container)
        layout.addWidget(self.pause_resume_button)
        layout.addStretch(0)  # Add a small stretch to push content up
        return box
    
    def toggle_pause_resume(self):
        """
        Checks the engine's current state and calls the appropriate
        pause() or resume() method.
        """
        if self.engine.is_running:
            self.engine.pause()
        else:
            self.engine.resume()

    def _create_statistics_box(self) -> QGroupBox:
        box = QGroupBox("Statistics")
        self._add_card_shadow(box)
        layout = QVBoxLayout(box)
        layout.setSpacing(15)
        
        # Today's files stat
        today_container = QWidget()
        today_layout = QHBoxLayout(today_container)
        today_layout.setContentsMargins(0, 0, 0, 0)
        
        today_icon = QLabel("📊")
        today_icon.setStyleSheet("font-size: 24px;")
        today_icon.setFixedWidth(40)
        
        today_info = QVBoxLayout()
        today_info.setSpacing(2)
        self.today_number = QLabel("0")
        self.today_number.setStyleSheet("font-size: 28px; font-weight: bold; color: #7aa2f7; margin: 0;")
        today_text = QLabel("Files Today")
        today_text.setStyleSheet("font-size: 14px; color: #a9b1d6; margin: 0;")
        today_info.addWidget(self.today_number)
        today_info.addWidget(today_text)
        
        today_layout.addWidget(today_icon)
        today_layout.addLayout(today_info)
        today_layout.addStretch()
        
        # Total organized stat
        total_container = QWidget()
        total_layout = QHBoxLayout(total_container)
        total_layout.setContentsMargins(0, 0, 0, 0)
        
        total_icon = QLabel("🎯")
        total_icon.setStyleSheet("font-size: 24px;")
        total_icon.setFixedWidth(40)
        
        total_info = QVBoxLayout()
        total_info.setSpacing(2)
        self.total_number = QLabel("0")
        self.total_number.setStyleSheet("font-size: 28px; font-weight: bold; color: #9ece6a; margin: 0;")
        total_text = QLabel("Total Organized")
        total_text.setStyleSheet("font-size: 14px; color: #a9b1d6; margin: 0;")
        total_info.addWidget(self.total_number)
        total_info.addWidget(total_text)
        
        total_layout.addWidget(total_icon)
        total_layout.addLayout(total_info)
        total_layout.addStretch()
        
        layout.addWidget(today_container)
        layout.addWidget(total_container)
        return box


    def _create_activity_feed_box(self) -> QGroupBox:
        box = QGroupBox("Live Activity Feed")
        self._add_card_shadow(box)
        layout = QVBoxLayout(box)
        
        self.activity_feed = QTextEdit()
        self.activity_feed.setReadOnly(True)
        self.activity_feed.setStyleSheet("""
            QTextEdit {
                background-color: #181926;
                border: 1.5px solid #363a4f;
                border-radius: 16px;
                color: #a9b1d6;
                font-size: 14px;
                padding: 16px;
                font-family: 'Consolas', 'Monaco', monospace;
                line-height: 1.4;
            }
        """)
        
        # Add a clear button
        clear_button = QPushButton("Clear Feed")
        clear_button.setStyleSheet("""
            QPushButton {
                background: #414868;
                color: #a9b1d6;
                border: 1px solid #545c7e;
                font-size: 13px;
                padding: 6px 16px;
                margin: 4px 0;
            }
            QPushButton:hover {
                background: #545c7e;
                color: #ffffff;
            }
        """)
        clear_button.clicked.connect(self.activity_feed.clear)
        
        layout.addWidget(self.activity_feed)
        layout.addWidget(clear_button)
        return box
    
    def _create_folder_decisions_box(self) -> QGroupBox:
        box = QGroupBox("Recent Folder Decisions")
        self._add_card_shadow(box)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        content_widget = QWidget()
        self.folder_decisions_layout = QVBoxLayout(content_widget)
        self.folder_decisions_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(content_widget)
        box_layout = QVBoxLayout(box)
        box_layout.addWidget(scroll_area)
        return box


    def _connect_signals(self):
        signals.log_message.connect(self.add_log_message)
        signals.update_stats.connect(self.update_statistics)
        signals.status_changed.connect(self.update_status)
        signals.file_organized.connect(self.on_file_organized)
        signals.folder_decision_made.connect(self.add_folder_decision)


    def add_log_message(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color code different message types
        if "ERROR" in message.upper() or "FAILED" in message.upper():
            color = "#f7768e"  # Red for errors
            icon = "❌"
        elif "WARNING" in message.upper():
            color = "#e0af68"  # Yellow for warnings
            icon = "⚠️"
        elif "MOVED" in message.upper() or "ORGANIZED" in message.upper():
            color = "#9ece6a"  # Green for success
            icon = "✅"
        elif "PROCESSING" in message.upper() or "SCANNING" in message.upper():
            color = "#7aa2f7"  # Blue for processing
            icon = "🔄"
        else:
            color = "#a9b1d6"  # Default color
            icon = "ℹ️"
        
        formatted_message = f'<span style="color: #545c7e;">[{timestamp}]</span> <span style="color: {color};">{icon} {message}</span>'
        self.activity_feed.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.activity_feed.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def update_statistics(self, today_count: int, total_count: int):
        self.today_number.setText(str(today_count))
        self.total_number.setText(str(total_count))

    def update_status(self, is_running: bool):
        """Updates the status label AND the pause/resume button text."""
        if is_running:
            self.status_label.setText("Active")
            self.status_label.setProperty("paused", "false")
            self.status_icon.setText("✅")
            self.pause_resume_button.setText("⏸️ Pause Watching")
        else:
            self.status_label.setText("Paused")
            self.status_label.setProperty("paused", "true")
            self.status_icon.setText("⏸️")
            self.pause_resume_button.setText("▶️ Resume Watching")
            
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def on_file_organized(self, category_name: str):
        # Refresh category data from database
        self.category_counts = statistics_db.get_category_stats_today()
        self.chart_update_timer.start()
        
    def add_folder_decision(self, original_path: str, new_path: str, category: str):
        decision_widget = FolderDecisionWidget(self.engine, original_path, new_path, category)
        self.folder_decisions_layout.insertWidget(0, decision_widget)

    def redraw_dashboard_charts(self):
        if not self.category_counts:
            self.chart_widget.update_slices([])
            return

        total = sum(self.category_counts.values())
        if total == 0:
            self.chart_widget.update_slices([])
            return
            
        sorted_data = dict(sorted(self.category_counts.items(), key=lambda item: item[1], reverse=True))
        
        slices_to_draw = []
        start_angle = 90.0

        for i, (category, count) in enumerate(sorted_data.items()):
            span_angle = (count / total) * 360.0
            color = self.chart_colors[i % len(self.chart_colors)]
            slices_to_draw.append({'color': color, 'start_angle': start_angle, 'span_angle': -span_angle})
            start_angle -= span_angle
        
        self.chart_widget.update_slices(slices_to_draw)
        
        while self.legend_layout.count():
            child = self.legend_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    nested_child = child.layout().takeAt(0)
                    if nested_child.widget(): nested_child.widget().deleteLater()
        
        for i, (category, count) in enumerate(sorted_data.items()):
            color = self.chart_colors[i % len(self.chart_colors)]
            self._add_legend_item(category, count, total, color)
            
    def _add_legend_item(self, name, value, total, color):
        # Create a container widget for better styling
        item_widget = QWidget()
        item_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(26,27,38,0.8);
                border-radius: 8px;
                padding: 8px;
                margin: 2px 0;
            }
            QWidget:hover {
                background-color: rgba(35,36,58,0.9);
            }
        """)
        
        legend_item_layout = QHBoxLayout(item_widget)
        legend_item_layout.setContentsMargins(8, 6, 8, 6)
        legend_item_layout.setSpacing(12)
        
        # Color indicator - make it larger and more prominent
        color_box = QLabel()
        color_box.setFixedSize(16, 16)
        color_box.setStyleSheet(f"""
            background-color: {color.name()};
            border-radius: 8px;
            border: 2px solid rgba(255,255,255,0.1);
        """)
        
        # Text container for category info
        text_container = QVBoxLayout()
        text_container.setSpacing(2)
        text_container.setContentsMargins(0, 0, 0, 0)
        
        # Category name
        category_label = QLabel(name)
        category_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #c0c5ea; margin: 0;")
        
        # Statistics
        percentage = (value / total) * 100
        stats_text = f"{value} files ({percentage:.1f}%)"
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-size: 12px; color: #9aa5ce; margin: 0;")
        
        text_container.addWidget(category_label)
        text_container.addWidget(stats_label)
        
        # Progress bar for visual percentage
        progress_container = QWidget()
        progress_container.setFixedHeight(4)
        progress_container.setStyleSheet(f"""
            background-color: rgba(35,36,58,0.5);
            border-radius: 2px;
        """)
        
        progress_bar = QWidget(progress_container)
        progress_width = int((percentage / 100) * 60)  # Max width of 60px
        progress_bar.setFixedSize(progress_width, 4)
        progress_bar.setStyleSheet(f"""
            background-color: {color.name()};
            border-radius: 2px;
        """)
        
        legend_item_layout.addWidget(color_box)
        legend_item_layout.addLayout(text_container, 1)
        legend_item_layout.addWidget(progress_container)
        
        self.legend_layout.addWidget(item_widget)

    def show_update_notification(self, update_info):
        """Show update notification using the modern dialog."""
        try:
            # Close any existing notification
            if self.update_notification:
                self.update_notification.close()
            
            # Create new notification widget
            self.update_notification = UpdateNotificationWidget(update_info, self)
            self.update_notification.show_update_dialog.connect(self._show_update_dialog)
            self.update_notification.show()
            
        except Exception as e:
            self.logger.error(f"Failed to show update notification: {e}")
    
    def _show_update_dialog(self, update_info):
        """Show the detailed update dialog."""
        try:
            dialog = UpdateDialog(update_info, self)
            dialog.download_requested.connect(self._handle_update_download)
            dialog.exec()
        except Exception as e:
            self.logger.error(f"Failed to show update dialog: {e}")
    
    def _handle_update_download(self, download_url):
        """Handle update download request."""
        try:
            # Import UpdateDialog locally to avoid circular imports
            from .update_dialog import UpdateDialog
            from PySide6.QtWidgets import QApplication
            
            # Store reference to current dialog
            current_dialog = None
            for widget in QApplication.allWidgets():
                if isinstance(widget, UpdateDialog) and widget.isVisible():
                    current_dialog = widget
                    break
            
            if current_dialog:
                # Connect progress updates to the dialog
                update_manager.current_update_info = {"download_url": download_url}
                update_manager.current_dialog = current_dialog
                
                # Start the download using the handle method instead
                update_manager._handle_download_request(download_url)
                
                # Connect progress signals after creating the download thread
                if hasattr(update_manager, 'download_thread'):
                    update_manager.download_thread.progress_updated.connect(current_dialog.update_progress)
            else:
                # Fallback to original method
                update_manager.current_update_info = {"download_url": download_url}
                update_manager._start_update_process()
        except Exception as e:
            self.logger.error(f"Failed to handle update download: {e}")
    
    def _on_update_error(self, error_message):
        """Handle update check errors."""
        self.logger.error(f"Update check failed: {error_message}")
        # Optionally show a user-friendly message for manual check failures
        if not getattr(update_manager, 'silent_check', True):
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Update Check Failed", 
                              f"Failed to check for updates:\n{error_message}")

    def _create_tray_icon(self):
        # --- MODIFIED: Use the absolute path for the icon ---
        icon_path = get_absolute_path("icon.png")
        
        if not os.path.exists(icon_path):
            self.logger.warning(f"Icon file 'icon.png' not found in the project directory.")
            self.logger.warning("Using a default system icon as a fallback. Please add 'icon.png' for a custom icon.")
            icon = self.style().standardIcon(getattr(self.style(), 'SP_DesktopIcon'))
        else:
            icon = QIcon(icon_path)
            
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("TidyCore")
        
        menu = QMenu()
        show_action = QAction("Show Dashboard", self)
        update_action = QAction("Check for Updates", self)
        quit_action = QAction("Quit TidyCore", self)

        show_action.triggered.connect(self.show_window)
        update_action.triggered.connect(lambda: update_manager.check_for_updates(silent=False))
        quit_action.triggered.connect(self.app.quit)

        menu.addAction(show_action)
        menu.addAction(update_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
    
    def show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        """Handle the window close event."""
        if hasattr(self, 'engine') and self.engine:
            self.engine.stop()
        
        # Hide to tray instead of closing if not explicitly exiting
        if not getattr(self, '_force_exit', False):
            event.ignore()
            self.hide()
            if not hasattr(self, '_first_hide'):
                self._first_hide = True
                self.tray_icon.showMessage(
                    "TidyCore",
                    "Application was minimized to tray",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        else:
            event.accept()

    def _exit_application(self):
        """Exit the application completely."""
        self._force_exit = True
        
        # Stop the engine
        if hasattr(self, 'engine') and self.engine:
            self.engine.stop()
        
        # Close the application
        QApplication.quit()