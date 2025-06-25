# tidycore/gui.py
import sys
import os
import logging
import qtawesome as qta
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QGroupBox, QTextEdit,
    QButtonGroup, QSystemTrayIcon, QMenu, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction, QColor, QFont

from tidycore.signals import signals
from tidycore.pie_chart_widget import PieChartWidget
from tidycore.folder_decision_widget import FolderDecisionWidget
from tidycore.settings_page import SettingsPage
# --- NEW: Import the AboutPage ---
from tidycore.about_page import AboutPage

# STYLESHEET is now more detailed
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
/* ---- QGroupBox Polish ---- */
QGroupBox {
    background-color: #24283b;
    border-radius: 8px;
    border: none; /* Remove the default border */
    margin-top: 15px; /* More space for the title */
    padding-top: 15px;
    font-size: 14px;
    font-weight: bold;
    color: #c0c5ea;
}
/* We will draw the title manually for more control */
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 20px; /* Indent title to make space for icon */
}

/* ... (QLabel, QTextEdit styles are the same) ... */
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

        self.setWindowTitle("TidyCore")
        self.setMinimumSize(950, 700) # Slightly larger for better spacing
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

        # --- NEW: About Button ---
        self.about_button = QPushButton("  About")
        self.about_button.setIcon(qta.icon("fa5s.info-circle"))
        self.about_button.setCheckable(True)
        
        # Add all buttons to the exclusive group
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)
        self.nav_button_group.addButton(self.dashboard_button)
        self.nav_button_group.addButton(self.settings_button)
        self.nav_button_group.addButton(self.about_button)
        
        self.dashboard_button.setChecked(True) # Default page

        # Add all buttons to the layout
        sidebar_layout.addWidget(title_label)
        sidebar_layout.addWidget(self.dashboard_button)
        sidebar_layout.addWidget(self.settings_button)
        sidebar_layout.addWidget(self.about_button) # Add to layout

        # Connect all buttons to switch pages
        self.dashboard_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.settings_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.about_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2)) # Connect new button
        
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

        # Set stretch factors to control sizing
        layout.setColumnStretch(0, 2) # Chart column is twice as wide
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)    # Status row
        layout.setRowStretch(1, 1)    # Stats row
        layout.setRowStretch(2, 2)    # Activity feed is twice as tall

        return page


    def _create_chart_box(self) -> QGroupBox:
        """Creates the box for the category breakdown chart."""
        box = QGroupBox("Category Breakdown")
        layout = QHBoxLayout(box)

        self.chart_widget = PieChartWidget()
        
        # This layout will hold the text legend
        self.legend_layout = QVBoxLayout()
        self.legend_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.legend_layout.setSpacing(10)
        
        layout.addWidget(self.chart_widget, 2)
        layout.addLayout(self.legend_layout, 1)
        
        return box


    def _create_status_box(self) -> QGroupBox:
        """Creates the main status and quick actions box."""
        box = QGroupBox("Status")
        layout = QVBoxLayout(box)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Initializing...")
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # We will use a single button and change its text
        self.pause_resume_button = QPushButton("Pause Watching")
        self.pause_resume_button.setFixedWidth(150) # Give it a nice fixed size
        
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)

        layout.addWidget(self.status_label)
        layout.addWidget(self.pause_resume_button)
        
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
    
    def _create_folder_decisions_box(self) -> QGroupBox:
        box = QGroupBox("Recent Folder Decisions")
        
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
        self.activity_feed.insertPlainText(f"{message}\n")

    def update_statistics(self, today_count: int, total_count: int):
        self.stats_label.setText(f"Files Today: {today_count}\nTotal Organized: {total_count}")

    def update_status(self, is_running: bool):
        """Updates the status label AND the pause/resume button text."""
        if is_running:
            self.status_label.setText("Active")
            self.status_label.setProperty("paused", "false")
            self.pause_resume_button.setText("Pause Watching")
        else:
            self.status_label.setText("Paused")
            self.status_label.setProperty("paused", "true")
            self.pause_resume_button.setText("Resume Watching")
            
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def on_file_organized(self, category_name: str):
        self.category_counts[category_name] = self.category_counts.get(category_name, 0) + 1
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
        legend_item_layout = QHBoxLayout()
        color_box = QLabel()
        color_box.setFixedSize(12, 12)
        color_box.setStyleSheet(f"background-color: {color.name()}; border-radius: 6px;")
        
        percentage = (value / total) * 100
        label_text = f"{name}: {value} ({percentage:.1f}%)"
        text_label = QLabel(label_text)
        
        legend_item_layout.addWidget(color_box)
        legend_item_layout.addWidget(text_label)
        legend_item_layout.addStretch()
        
        self.legend_layout.addLayout(legend_item_layout)

    def _create_tray_icon(self):
        icon_path = os.path.join(os.getcwd(), "icon.png")
        
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
        quit_action = QAction("Quit TidyCore", self)

        show_action.triggered.connect(self.show_window)
        quit_action.triggered.connect(self.app.quit)

        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
    
    def show_window(self):
        self.show()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        if self.isVisible():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "TidyCore",
                "TidyCore is still running in the background.",
                QSystemTrayIcon.Information,
                2000
            )