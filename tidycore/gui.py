# tidycore/gui.py
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QLabel,
    QPushButton, QGroupBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon # We will need this later for icons

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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TidyCore Dashboard")
        self.setMinimumSize(800, 600)

        # Apply the modern stylesheet to the entire window
        self.setStyleSheet(MODERN_STYLESHEET)
        
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.grid_layout = QGridLayout(central_widget)

        # Create and add the bento boxes to the grid
        self._create_status_box()
        self._create_chart_box()
        self._create_activity_feed_box()
        self._create_folder_decisions_box()
        self._create_statistics_box()
        self._create_settings_box()

    def _create_status_box(self) -> None:
        """Creates the main status and quick actions box."""
        box = QGroupBox("Status & Quick Actions")
        layout = QGridLayout(box)

        status_label = QLabel("Actively Watching")
        status_label.setObjectName("StatusLabel") # For specific styling
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pause_button = QPushButton("Pause Watching")
        organize_button = QPushButton("Organize Now")

        layout.addWidget(status_label, 0, 0, 1, 2)
        layout.addWidget(pause_button, 1, 0)
        layout.addWidget(organize_button, 1, 1)

        self.grid_layout.addWidget(box, 0, 0, 1, 2) # Span 1 row, 2 columns

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

        placeholder_label = QLabel("Moved 'invoice.pdf' to 'Documents/PDFs'\nMoved 'vacation.jpg' to 'Images'")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(placeholder_label)

        self.grid_layout.addWidget(box, 1, 0, 2, 2) # Span 2 rows, 2 columns

    def _create_folder_decisions_box(self) -> None:
        """Creates the box for recent folder decisions."""
        box = QGroupBox("Recent Folder Decisions")
        layout = QGridLayout(box)
        
        placeholder_label = QLabel("No recent folder decisions to show.")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(placeholder_label)

        self.grid_layout.addWidget(box, 1, 2, 2, 1) # Span 2 rows, 1 column

    def _create_statistics_box(self) -> None:
        """Creates the box for key statistics."""
        box = QGroupBox("Statistics")
        layout = QGridLayout(box)
        
        placeholder_label = QLabel("Files Today: 42\nTotal Organized: 1,821")
        layout.addWidget(placeholder_label)

        self.grid_layout.addWidget(box, 3, 0, 1, 1)

    def _create_settings_box(self) -> None:
        """Creates the box for settings and logs navigation."""
        box = QGroupBox("Settings & Logs")
        layout = QGridLayout(box)

        settings_button = QPushButton("Settings")
        logs_button = QPushButton("View Full Log")
        
        layout.addWidget(settings_button, 0, 0)
        layout.addWidget(logs_button, 0, 1)

        self.grid_layout.addWidget(box, 3, 1, 1, 2) # Span 1 row, 2 columns

# This allows you to run this file directly to test the GUI, if needed
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TidyCoreGUI()
    window.show()
    sys.exit(app.exec())