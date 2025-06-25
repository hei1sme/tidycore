# tidycore/settings_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton
)
from PySide6.QtCore import Qt

from tidycore.config_manager import ConfigManager
from tidycore.signals import signals

class SettingsPage(QWidget):
    """The main settings page for TidyCore."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.current_config = {} # Will be populated by refresh_settings

        # Initial UI build
        self._build_ui()
        
        # Load the initial data into the UI
        self.refresh_settings()

        # Connect to the config changed signal to stay in sync
        signals.config_changed.connect(self.refresh_settings)

    def _build_ui(self):
        """Creates the static UI elements once."""
        page_layout = QVBoxLayout(self)
        
        target_folder_box = self._create_target_folder_section()
        # --- NEW: Create the folder strategy box ---
        folder_strategy_box = self._create_folder_strategy_section()
        ignore_list_box = self._create_ignore_list_section()
        
        page_layout.addWidget(target_folder_box)
        page_layout.addWidget(folder_strategy_box) # Add it to the layout
        page_layout.addWidget(ignore_list_box)
        page_layout.addStretch()

        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._save_settings)
        save_button_layout.addWidget(save_button)
        page_layout.addLayout(save_button_layout)

    def refresh_settings(self):
        """
        Loads the latest config from disk and populates the UI controls.
        This is called on initialization and whenever the config_changed signal is emitted.
        """
        self.current_config = self.config_manager.load_config()
        
        # Populate target folder
        self.folder_path_edit.setText(self.current_config.get("target_folder", ""))
        
        # --- NEW: Set the correct radio button ---
        strategy = self.current_config.get("folder_handling_strategy", "smart_scan")
        if strategy == "move_to_others":
            self.move_to_others_radio.setChecked(True)
        elif strategy == "ignore":
            self.ignore_folders_radio.setChecked(True)
        else: # Default to smart_scan
            self.smart_scan_radio.setChecked(True)
            
        # Populate ignore list
        self.ignore_list_widget.clear()
        ignore_items = self.current_config.get("ignore_list", [])
        for item in ignore_items:
            self.ignore_list_widget.addItem(QListWidgetItem(item))

    def _create_target_folder_section(self) -> QGroupBox:
        """Creates the UI for the target folder setting without loading data."""
        box = QGroupBox("Target Folder")
        layout = QHBoxLayout(box)

        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setReadOnly(True)

        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_for_folder)

        layout.addWidget(self.folder_path_edit)
        layout.addWidget(browse_button)
        return box

    def _browse_for_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
        if folder_name:
            self.folder_path_edit.setText(folder_name)

    # --- NEW METHOD to create the UI section ---
    def _create_folder_strategy_section(self) -> QGroupBox:
        box = QGroupBox("Folder Handling Strategy")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)

        self.smart_scan_radio = QRadioButton("Smart Categorization (Default)")
        self.smart_scan_radio.setToolTip("Scan inside unknown folders to determine the best category.")
        
        self.move_to_others_radio = QRadioButton("Move to 'Others' Folder")
        self.move_to_others_radio.setToolTip("Move any unknown folder directly into the 'Others' category without scanning.")
        
        self.ignore_folders_radio = QRadioButton("Ignore All Folders")
        self.ignore_folders_radio.setToolTip("Only organize loose files. Do not move any folders.")
        
        layout.addWidget(self.smart_scan_radio)
        layout.addWidget(self.move_to_others_radio)
        layout.addWidget(self.ignore_folders_radio)
        
        return box

    def _create_ignore_list_section(self) -> QGroupBox:
        """Creates the UI for the ignore list setting without loading data."""
        box = QGroupBox("Ignored Files & Folders")
        layout = QGridLayout(box)

        self.ignore_list_widget = QListWidget()

        self.new_ignore_item_edit = QLineEdit()
        self.new_ignore_item_edit.setPlaceholderText("Enter item to ignore (e.g., 'myfile.txt' or '.tmp')")
        add_button = QPushButton("Add")
        remove_button = QPushButton("Remove Selected")

        add_button.clicked.connect(self._add_ignore_item)
        remove_button.clicked.connect(self._remove_ignore_item)
        
        layout.addWidget(self.ignore_list_widget, 0, 0, 1, 2)
        layout.addWidget(self.new_ignore_item_edit, 1, 0)
        layout.addWidget(add_button, 1, 1)
        layout.addWidget(remove_button, 2, 1)
        layout.setColumnStretch(0, 1)
        return box
        
    def _add_ignore_item(self):
        item_text = self.new_ignore_item_edit.text().strip()
        if item_text:
            # Check for duplicates before adding
            if not self.ignore_list_widget.findItems(item_text, Qt.MatchFlag.MatchExactly):
                self.ignore_list_widget.addItem(QListWidgetItem(item_text))
                self.new_ignore_item_edit.clear()
            
    def _remove_ignore_item(self):
        for item in self.ignore_list_widget.selectedItems():
            self.ignore_list_widget.takeItem(self.ignore_list_widget.row(item))

    def _save_settings(self):
        """Gathers data from UI, saves to config, and signals that the config has changed."""
        self.current_config["target_folder"] = self.folder_path_edit.text()
        
        # --- NEW: Get the selected strategy and save it ---
        strategy = "smart_scan" # Default
        if self.move_to_others_radio.isChecked():
            strategy = "move_to_others"
        elif self.ignore_folders_radio.isChecked():
            strategy = "ignore"
        self.current_config["folder_handling_strategy"] = strategy
        
        new_ignore_list = [self.ignore_list_widget.item(i).text() for i in range(self.ignore_list_widget.count())]
        self.current_config["ignore_list"] = new_ignore_list
        
        try:
            self.config_manager.save_config(self.current_config)
            QMessageBox.information(self, "Success", "Settings saved. The engine will restart automatically if needed.")
            # Emit the signal to notify everyone (including ourselves and the engine)
            signals.config_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")