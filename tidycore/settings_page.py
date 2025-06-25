# tidycore/settings_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton, QTreeWidget, QTreeWidgetItem
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
        
        # We will create a two-column layout for settings
        main_grid = QGridLayout()
        
        # Left column
        target_folder_box = self._create_target_folder_section()
        folder_strategy_box = self._create_folder_strategy_section()
        ignore_list_box = self._create_ignore_list_section()
        
        # Right column (the new Rules Editor)
        rules_editor_box = self._create_rules_editor_section()

        main_grid.addWidget(target_folder_box, 0, 0)
        main_grid.addWidget(folder_strategy_box, 1, 0)
        main_grid.addWidget(ignore_list_box, 2, 0)
        main_grid.addWidget(rules_editor_box, 0, 1, 3, 1) # Span all 3 rows
        main_grid.setColumnStretch(0, 1)
        main_grid.setColumnStretch(1, 2) # Make the rules editor wider
        
        page_layout.addLayout(main_grid)
        
        # Save Button
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._save_settings)
        save_button_layout.addWidget(save_button)
        page_layout.addLayout(save_button_layout)

    def refresh_settings(self):
        """
        Loads the latest config from disk and populates all UI controls.
        """
        self.current_config = self.config_manager.load_config()
        
        # Populate target folder
        self.folder_path_edit.setText(self.current_config.get("target_folder", ""))
        
        # Populate folder handling strategy
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
            
        # --- NEW: Populate the rules tree ---
        self._populate_rules_tree()

    def _create_target_folder_section(self) -> QGroupBox:
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

    # --- NEW METHOD to create the Rules Editor ---
    def _create_rules_editor_section(self) -> QGroupBox:
        box = QGroupBox("File Type Rules")
        layout = QVBoxLayout(box)

        self.rules_tree = QTreeWidget()
        self.rules_tree.setHeaderLabels(["Category / Extension"])
        self.rules_tree.setAlternatingRowColors(True)

        button_layout = QHBoxLayout()
        add_category_btn = QPushButton("Add Category...")
        add_extension_btn = QPushButton("Add Extension...")
        remove_btn = QPushButton("Remove Selected")
        
        button_layout.addWidget(add_category_btn)
        button_layout.addWidget(add_extension_btn)
        button_layout.addStretch()
        button_layout.addWidget(remove_btn)
        
        layout.addWidget(self.rules_tree)
        layout.addLayout(button_layout)
        
        # For now, disable buttons until we implement the logic
        add_category_btn.setEnabled(False)
        add_extension_btn.setEnabled(False)
        remove_btn.setEnabled(False)

        return box

    # --- NEW METHOD to build the tree from the config ---
    def _populate_rules_tree(self):
        self.rules_tree.clear()
        rules = self.current_config.get("rules", {})
        
        for category, sub_rules in rules.items():
            # Create a top-level item for the main category
            category_item = QTreeWidgetItem(self.rules_tree, [category])
            category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsEditable)

            if isinstance(sub_rules, dict): # Nested categories (e.g., Documents)
                for sub_category, extensions in sub_rules.items():
                    sub_item = QTreeWidgetItem(category_item, [sub_category])
                    sub_item.setFlags(sub_item.flags() | Qt.ItemFlag.ItemIsEditable)
                    for ext in extensions:
                        ext_item = QTreeWidgetItem(sub_item, [ext])
                        ext_item.setFlags(ext_item.flags() | Qt.ItemFlag.ItemIsEditable)
            elif isinstance(sub_rules, list): # Flat categories (e.g., Images)
                for ext in sub_rules:
                    ext_item = QTreeWidgetItem(category_item, [ext])
                    ext_item.setFlags(ext_item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        self.rules_tree.expandAll()

    def _create_ignore_list_section(self) -> QGroupBox:
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
        if item_text and not self.ignore_list_widget.findItems(item_text, Qt.MatchFlag.MatchExactly):
            self.ignore_list_widget.addItem(QListWidgetItem(item_text))
            self.new_ignore_item_edit.clear()
            
    def _remove_ignore_item(self):
        for item in self.ignore_list_widget.selectedItems():
            self.ignore_list_widget.takeItem(self.ignore_list_widget.row(item))

    def _save_settings(self):
        """Gathers all data from UI, saves to config, and signals the change."""
        # Save target folder
        self.current_config["target_folder"] = self.folder_path_edit.text()
        
        # Save folder handling strategy
        strategy = "smart_scan"
        if self.move_to_others_radio.isChecked():
            strategy = "move_to_others"
        elif self.ignore_folders_radio.isChecked():
            strategy = "ignore"
        self.current_config["folder_handling_strategy"] = strategy

        # --- NEW: Logic to rebuild the rules dictionary from the tree ---
        new_rules = {}
        for i in range(self.rules_tree.topLevelItemCount()):
            category_item = self.rules_tree.topLevelItem(i)
            category_name = category_item.text(0)
            
            # Check if it has sub-categories or direct extensions
            if category_item.childCount() > 0 and category_item.child(0).childCount() > 0:
                # Nested structure
                sub_categories = {}
                for j in range(category_item.childCount()):
                    sub_item = category_item.child(j)
                    sub_name = sub_item.text(0)
                    extensions = [sub_item.child(k).text(0) for k in range(sub_item.childCount())]
                    sub_categories[sub_name] = extensions
                new_rules[category_name] = sub_categories
            else:
                # Flat structure
                extensions = [category_item.child(k).text(0) for k in range(category_item.childCount())]
                new_rules[category_name] = extensions
                
        self.current_config["rules"] = new_rules

        # Save ignore list
        new_ignore_list = [self.ignore_list_widget.item(i).text() for i in range(self.ignore_list_widget.count())]
        self.current_config["ignore_list"] = new_ignore_list
        
        try:
            self.config_manager.save_config(self.current_config)
            QMessageBox.information(self, "Success", "Settings saved. The engine will restart automatically if needed.")
            signals.config_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")