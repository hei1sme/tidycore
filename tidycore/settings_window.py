# tidycore/settings_window.py
import sys
from PySide6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

class SettingsWindow(QDialog):
    """A dialog window for configuring TidyCore settings."""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TidyCore Settings")
        self.setMinimumSize(600, 400)
        self.config_manager = config_manager
        self.current_config = self.config_manager.load_config()

        # Main layout
        self.layout = QVBoxLayout(self)

        # Create UI sections
        self._create_target_folder_section()
        self._create_ignore_list_section()
        self.layout.addStretch()  # Pushes buttons to the bottom
        self._create_action_buttons()

        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #c0c5ea; font-size: 14px; }
            QLineEdit, QListWidget { 
                background-color: #27293d; 
                color: #f8f8f2; 
                border: 1px solid #3a3c5a;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff79c6, stop:1 #bd93f9);
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 13px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff92d0, stop:1 #c9a3fa); }
        """)

    def _create_target_folder_section(self):
        """Creates the UI for setting the target folder."""
        label = QLabel("Folder to Organize:")
        self.layout.addWidget(label)

        h_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setText(self.current_config.get("target_folder", ""))
        self.folder_path_edit.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_for_folder)

        h_layout.addWidget(self.folder_path_edit)
        h_layout.addWidget(browse_button)
        self.layout.addLayout(h_layout)

    def _browse_for_folder(self):
        """Opens a dialog to select a directory."""
        folder_name = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
        if folder_name:
            self.folder_path_edit.setText(folder_name)

    def _create_ignore_list_section(self):
        """Creates the UI for managing the ignore list."""
        label = QLabel("Ignored Files and Extensions (one per line):")
        self.layout.addWidget(label)

        self.ignore_list_widget = QListWidget()
        self.ignore_list_widget.setAlternatingRowColors(True)
        # Populate the list
        ignore_items = self.current_config.get("ignore_list", [])
        for item in ignore_items:
            self.ignore_list_widget.addItem(QListWidgetItem(item))

        self.layout.addWidget(self.ignore_list_widget)

        # Add/Remove buttons
        h_layout = QHBoxLayout()
        self.new_ignore_item_edit = QLineEdit()
        self.new_ignore_item_edit.setPlaceholderText("Enter item to ignore (e.g., 'myfile.txt' or '.tmp')")
        add_button = QPushButton("Add")
        remove_button = QPushButton("Remove Selected")

        add_button.clicked.connect(self._add_ignore_item)
        remove_button.clicked.connect(self._remove_ignore_item)
        
        h_layout.addWidget(self.new_ignore_item_edit)
        h_layout.addWidget(add_button)
        h_layout.addWidget(remove_button)
        self.layout.addLayout(h_layout)
        
    def _add_ignore_item(self):
        """Adds a new item to the ignore list widget."""
        item_text = self.new_ignore_item_edit.text().strip()
        if item_text:
            self.ignore_list_widget.addItem(QListWidgetItem(item_text))
            self.new_ignore_item_edit.clear()
            
    def _remove_ignore_item(self):
        """Removes the selected item from the ignore list widget."""
        selected_items = self.ignore_list_widget.selectedItems()
        if not selected_items: return
        for item in selected_items:
            self.ignore_list_widget.takeItem(self.ignore_list_widget.row(item))

    def _create_action_buttons(self):
        """Creates the Save and Cancel buttons."""
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Push buttons to the right

        cancel_button = QPushButton("Cancel")
        save_button = QPushButton("Save & Restart Engine")

        cancel_button.clicked.connect(self.reject) # Closes the dialog
        save_button.clicked.connect(self._save_settings)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        self.layout.addLayout(button_layout)
    
    def _save_settings(self):
        """Gathers data from UI, saves to config, and closes the dialog."""
        # Update target folder
        self.current_config["target_folder"] = self.folder_path_edit.text()
        
        # Update ignore list
        new_ignore_list = []
        for i in range(self.ignore_list_widget.count()):
            new_ignore_list.append(self.ignore_list_widget.item(i).text())
        self.current_config["ignore_list"] = new_ignore_list
        
        # Save the updated config
        try:
            self.config_manager.save_config(self.current_config)
            QMessageBox.information(self, "Success", "Settings saved. The TidyCore engine will restart to apply changes.")
            self.accept() # Close the dialog with an "OK" signal
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")