# tidycore/update_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QProgressBar, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont
import qtawesome as qta
from typing import Dict

class UpdateDialog(QDialog):
    """Dialog for notifying users about available updates."""
    
    download_requested = Signal(str)
    
    def __init__(self, update_info: Dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("TidyCore Update Available")
        self.setFixedSize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # Initialize logger
        import logging
        self.logger = logging.getLogger("TidyCore")
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        update_icon = QLabel("🔄")
        update_icon.setStyleSheet("font-size: 36px;")
        update_icon.setFixedSize(50, 50)
        update_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_layout = QVBoxLayout()
        title_label = QLabel("Update Available!")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #7aa2f7;")
        
        version_label = QLabel(f"Version {self.update_info['version']} is available")
        version_label.setStyleSheet("font-size: 14px; color: #a9b1d6;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()
        
        header_layout.addWidget(update_icon)
        header_layout.addLayout(title_layout, 1)
        
        layout.addLayout(header_layout)
        
        # Info section
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(35,36,58,0.8);
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        # Release info
        size_info = QLabel(f"📦 Size: {self.update_info.get('size', 'Unknown')}")
        size_info.setStyleSheet("font-size: 13px; color: #a9b1d6; margin: 5px 0;")
        
        date_info = QLabel(f"📅 Released: {self._format_date(self.update_info.get('published_at', ''))}")
        date_info.setStyleSheet("font-size: 13px; color: #a9b1d6; margin: 5px 0;")
        
        info_layout.addWidget(size_info)
        info_layout.addWidget(date_info)
        
        layout.addWidget(info_frame)
        
        # Changelog section
        changelog_label = QLabel("What's New:")
        changelog_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #c0c5ea; margin-top: 10px;")
        layout.addWidget(changelog_label)
        
        self.changelog_text = QTextEdit()
        self.changelog_text.setPlainText(self.update_info.get('changelog', 'No changelog available'))
        self.changelog_text.setMaximumHeight(120)
        self.changelog_text.setReadOnly(True)
        layout.addWidget(self.changelog_text)
        
        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3b3f51;
                border-radius: 8px;
                background-color: #1a1b26;
                text-align: center;
                color: #a9b1d6;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #7aa2f7, stop:1 #7dcfff);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Auto-update checkbox
        self.auto_update_checkbox = QCheckBox("Automatically check for updates")
        self.auto_update_checkbox.setChecked(True)
        self.auto_update_checkbox.setStyleSheet("""
            QCheckBox {
                color: #a9b1d6;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #3b3f51;
                background-color: #1a1b26;
            }
            QCheckBox::indicator:checked {
                background-color: #7aa2f7;
                border-color: #7aa2f7;
            }
        """)
        layout.addWidget(self.auto_update_checkbox)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.later_button = QPushButton("Later")
        self.later_button.setStyleSheet("""
            QPushButton {
                background: #414868;
                color: #a9b1d6;
                border: 1px solid #545c7e;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #545c7e;
                color: #ffffff;
            }
        """)
        self.later_button.clicked.connect(self.reject)
        
        self.download_button = QPushButton("Download & Install")
        self.download_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #7aa2f7, stop:1 #7dcfff);
                color: #23243a;
                border: none;
                font-size: 14px;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #bb9af7, stop:1 #7aa2f7);
                color: #fff;
            }
            QPushButton:disabled {
                background: #414868;
                color: #666;
            }
        """)
        self.download_button.clicked.connect(self._start_download)
        
        button_layout.addStretch()
        button_layout.addWidget(self.later_button)
        button_layout.addWidget(self.download_button)
        
        layout.addLayout(button_layout)
    
    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1b26;
                color: #a9b1d6;
                font-family: 'Segoe UI', 'Inter', 'Roboto', Arial, sans-serif;
            }
            QTextEdit {
                background-color: #181926;
                border: 1px solid #3b3f51;
                border-radius: 8px;
                color: #a9b1d6;
                font-size: 12px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
    
    def _format_date(self, date_str: str) -> str:
        """Format the release date."""
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%B %d, %Y")
        except:
            return "Unknown"
    
    def _start_download(self):
        """Start the download process."""
        self.download_button.setEnabled(False)
        self.download_button.setText("Downloading...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        download_url = self.update_info.get('download_url')
        if download_url:
            self.logger.info(f"Starting download from UpdateDialog: {download_url}")
            self.download_requested.emit(download_url)
        else:
            # If no download_url in update_info, try to construct it from version
            self.logger.error("No download URL found in update info")
            self.logger.error(f"Available keys in update_info: {list(self.update_info.keys())}")
            self.update_progress(-1)  # Show error
    
    def update_progress(self, progress: int):
        """Update the download progress."""
        if progress < 0:  # Error
            self.progress_bar.setVisible(False)
            self.download_button.setEnabled(True)
            self.download_button.setText("Download Failed - Retry")
            self.download_button.setStyleSheet("""
                QPushButton {
                    background: #f7768e;
                    color: #ffffff;
                    border: none;
                    font-size: 14px;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-weight: 600;
                }
            """)
        elif progress >= 100:  # Complete
            self.progress_bar.setValue(100)
            self.download_button.setText("Installing...")
            QTimer.singleShot(2000, self._installation_complete)
        else:  # In progress
            self.progress_bar.setValue(progress)
    
    def _installation_complete(self):
        """Handle installation completion."""
        self.download_button.setText("Restart Required")
        self.download_button.setEnabled(False)
        
        # Show restart message
        restart_label = QLabel("✅ Update downloaded! Restart TidyCore to apply the update.")
        restart_label.setStyleSheet("""
            QLabel {
                background-color: rgba(158, 206, 106, 0.2);
                border: 1px solid #9ece6a;
                border-radius: 8px;
                padding: 10px;
                color: #9ece6a;
                font-weight: bold;
            }
        """)
        
        # Insert before buttons
        layout = self.layout()
        layout.insertWidget(layout.count() - 1, restart_label)
    
    def get_auto_update_preference(self) -> bool:
        """Get the auto-update checkbox state."""
        return self.auto_update_checkbox.isChecked()


class UpdateNotificationWidget(QFrame):
    """Small notification widget for the main window."""
    
    show_update_dialog = Signal(dict)  # Emit update info to show detailed dialog
    
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setFixedHeight(60)
        self._setup_ui()
        self._apply_styles()
        self.hide()  # Hidden by default
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # Icon
        icon_label = QLabel("🔄")
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setFixedSize(30, 30)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        self.title_label = QLabel("Update Available")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #7aa2f7; margin: 0;")
        
        self.subtitle_label = QLabel("A new version of TidyCore is ready to install")
        self.subtitle_label.setStyleSheet("font-size: 12px; color: #a9b1d6; margin: 0;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        
        # Update button
        self.update_button = QPushButton("Update Now")
        self.update_button.setFixedSize(100, 35)
        self.update_button.clicked.connect(lambda: self.show_update_dialog.emit(self.update_info))
        
        # Close button
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(25, 25)
        self.close_button.clicked.connect(self.hide)
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self.update_button)
        layout.addWidget(self.close_button)
    
    def _apply_styles(self):
        self.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(122,162,247,0.15), stop:1 rgba(187,154,247,0.15));
                border: 1px solid #7aa2f7;
                border-radius: 12px;
                margin: 5px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #7aa2f7, stop:1 #7dcfff);
                color: #23243a;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #bb9af7, stop:1 #7aa2f7);
                color: #fff;
            }
            QPushButton#close_button {
                background: transparent;
                color: #a9b1d6;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#close_button:hover {
                background: #f7768e;
                color: #fff;
            }
        """)
        
        self.close_button.setObjectName("close_button")
    
    def show_update_notification(self, version: str):
        """Show the notification with version info."""
        self.subtitle_label.setText(f"Version {version} is available")
        self.show()
