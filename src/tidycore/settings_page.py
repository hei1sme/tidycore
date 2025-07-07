# tidycore/settings_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton, QTreeWidget, QTreeWidgetItem, QMenu,
    QInputDialog,
    # --- NEW: Add QCheckBox ---
    QCheckBox
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from .config_manager import ConfigManager
from .signals import signals
# --- NEW: Import the startup manager instance ---
from .startup_manager import startup_manager

class SettingsPage(QWidget):
    """The main settings page for TidyCore."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.current_config = {} # Will be populated by refresh_settings
        
        # Flag to prevent startup messages during initialization
        self._initializing = True

        # Initial UI build
        self._build_ui()
        
        # Load the initial data into the UI
        self.refresh_settings()
        
        # Mark initialization as complete
        self._initializing = False

        # Connect to the config changed signal to stay in sync
        signals.config_changed.connect(self.refresh_settings)

    def _build_ui(self):
        """Creates the static UI elements once."""
        page_layout = QVBoxLayout(self)
        
        # We will create a two-column layout for settings
        main_grid = QGridLayout()
        
        # Left column
        # --- General Settings Box ---
        general_box = self._create_general_settings_section()
        folder_strategy_box = self._create_folder_strategy_section()
        ignore_list_box = self._create_ignore_list_section()
        
        # Right column (the new Rules Editor)
        rules_editor_box = self._create_rules_editor_section()

        main_grid.addWidget(general_box, 0, 0) # Add the new box
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

        # --- NEW: Set the checkbox state (block all signals during update) ---
        self.startup_checkbox.blockSignals(True)
        self.startup_checkbox.setChecked(startup_manager.is_enabled())
        self.startup_checkbox.blockSignals(False)

    # --- NEW METHOD for the general settings box ---
    def _create_general_settings_section(self) -> QGroupBox:
        box = QGroupBox("General Settings")
        layout = QVBoxLayout(box)

        # Target folder part
        target_folder_layout = QHBoxLayout()
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setText(self.current_config.get("target_folder", ""))
        self.folder_path_edit.setReadOnly(True)
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_for_folder)
        target_folder_layout.addWidget(self.folder_path_edit)
        target_folder_layout.addWidget(browse_button)
        
        # Startup checkbox part
        self.startup_checkbox = QCheckBox("Launch TidyCore when computer starts")
        self.startup_checkbox.toggled.connect(self._handle_startup_toggle)
        
        layout.addLayout(target_folder_layout)
        layout.addWidget(self.startup_checkbox)
        
        return box

    def _browse_for_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
        if folder_name:
            self.folder_path_edit.setText(folder_name)

    # --- NEW METHOD to handle the checkbox logic ---
    def _handle_startup_toggle(self, checked: bool):
        # Don't show messages during initialization
        if self._initializing:
            return
            
        try:
            if checked:
                startup_manager.enable()
                QMessageBox.information(self, "Startup Enabled", "TidyCore will now start automatically when you log in.")
            else:
                startup_manager.disable()
                QMessageBox.information(self, "Startup Disabled", "TidyCore will no longer start automatically.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not update startup settings:\n{e}")

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

    def _create_rules_editor_section(self) -> QGroupBox:
        box = QGroupBox("File Type Rules (Right-click to edit)")
        layout = QVBoxLayout(box)

        self.rules_tree = QTreeWidget()
        self.rules_tree.setHeaderLabels(["Category / Extension"])
        self.rules_tree.setAlternatingRowColors(True)
        # Enable the context menu
        self.rules_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.rules_tree.customContextMenuRequested.connect(self._open_rules_context_menu)

        # --- NEW: A single button to add top-level categories ---
        add_category_btn = QPushButton("Add New Main Category...")
        add_category_btn.clicked.connect(self._add_top_level_category)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(add_category_btn)

        layout.addWidget(self.rules_tree)
        layout.addLayout(button_layout)
        
        return box

    def _open_rules_context_menu(self, position):
        menu = QMenu()
        selected_item = self.rules_tree.currentItem()

        if not selected_item:
            # Right-clicked on an empty area
            add_top_action = QAction("Add New Main Category...", self)
            add_top_action.triggered.connect(self._add_top_level_category)
            menu.addAction(add_top_action)
        else:
            # Determine if the item is an extension or a category
            # A simple rule: if it starts with '.', it's an extension.
            is_extension = selected_item.text(0).startswith('.')

            if is_extension:
                # If it's an extension, the only option is to remove it.
                pass # The remove action is added below for all items
            else:
                # If it's a category (main or sub), offer to add children to it.
                add_sub_cat_action = QAction("Add Sub-Category...", self)
                add_sub_cat_action.triggered.connect(lambda: self._add_item(selected_item, is_subcategory=True))
                
                add_ext_action = QAction("Add Extension...", self)
                add_ext_action.triggered.connect(lambda: self._add_item(selected_item, is_extension=True))
                
                menu.addAction(add_sub_cat_action)
                menu.addAction(add_ext_action)

            # Add a remove action for any selected item
            menu.addSeparator()
            remove_action = QAction("Remove Selected", self)
            remove_action.triggered.connect(lambda: self._remove_item(selected_item))
            menu.addAction(remove_action)

        # Execute the menu at the cursor's position
        menu.exec(self.rules_tree.viewport().mapToGlobal(position))

    def _add_top_level_category(self):
        text, ok = QInputDialog.getText(self, "Add Main Category", "Enter name for the new category:")
        if ok and text:
            item = QTreeWidgetItem(self.rules_tree, [text])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)

    def _add_item(self, parent_item: QTreeWidgetItem, is_subcategory=False, is_extension=False):
        title = "Add Item"
        prompt = "Enter name:"
        if is_subcategory:
            title, prompt = "Add Sub-Category", "Enter name for the sub-category:"
        elif is_extension:
            title, prompt = "Add Extension", "Enter extension (e.g., '.txt'):"

        text, ok = QInputDialog.getText(self, title, prompt)
        if ok and text:
            # Ensure extensions start with a dot
            if is_extension and not text.startswith('.'):
                text = '.' + text
            
            item = QTreeWidgetItem(parent_item, [text])
            # Only categories and sub-categories are editable by default
            if not is_extension:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
    
    def _remove_item(self, item_to_remove: QTreeWidgetItem):
        parent = item_to_remove.parent()
        if parent:
            parent.removeChild(item_to_remove)
        else: # It's a top-level item
            index = self.rules_tree.indexOfTopLevelItem(item_to_remove)
            self.rules_tree.takeTopLevelItem(index)

    # --- NEW, ROBUST POPULATING LOGIC ---
    def _populate_rules_tree(self):
        self.rules_tree.clear()
        rules = self.current_config.get("rules", {})
        
        for category, sub_rules in rules.items():
            category_item = QTreeWidgetItem(self.rules_tree, [category])
            category_item.setFlags(category_item.flags() | Qt.ItemFlag.ItemIsEditable)

            if isinstance(sub_rules, dict): # Nested categories
                for sub_key, extensions in sub_rules.items():
                    if sub_key == "__extensions__": # Our special key for flat extensions
                        for ext in extensions:
                            ext_item = QTreeWidgetItem(category_item, [ext])
                    else: # A true sub-category
                        sub_item = QTreeWidgetItem(category_item, [sub_key])
                        sub_item.setFlags(sub_item.flags() | Qt.ItemFlag.ItemIsEditable)
                        for ext in extensions:
                            ext_item = QTreeWidgetItem(sub_item, [ext])
            elif isinstance(sub_rules, list): # Purely flat categories
                for ext in sub_rules:
                    ext_item = QTreeWidgetItem(category_item, [ext])
        
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

    # --- NEW, ROBUST SAVING LOGIC ---
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
        
        new_rules = {}
        for i in range(self.rules_tree.topLevelItemCount()):
            category_item = self.rules_tree.topLevelItem(i)
            category_name = category_item.text(0)
            
            # This is the new, robust saving algorithm
            has_sub_categories = False
            flat_extensions = []
            nested_rules = {}
            
            for j in range(category_item.childCount()):
                child_item = category_item.child(j)
                # If a child has its own children, it's a sub-category
                if child_item.childCount() > 0:
                    has_sub_categories = True
                    sub_name = child_item.text(0)
                    extensions = [child_item.child(k).text(0) for k in range(child_item.childCount())]
                    nested_rules[sub_name] = extensions
                else: # It's a flat extension
                    flat_extensions.append(child_item.text(0))
            
            if has_sub_categories:
                # If there are any sub-categories, we must use the nested format.
                # Store any flat extensions under the special key.
                if flat_extensions:
                    nested_rules["__extensions__"] = flat_extensions
                new_rules[category_name] = nested_rules
            else:
                # If there are NO sub-categories, use the simple flat list format.
                new_rules[category_name] = flat_extensions

        self.current_config["rules"] = new_rules

        # Save ignore list
        new_ignore_list = [self.ignore_list_widget.item(i).text() for i in range(self.ignore_list_widget.count())]
        self.current_config["ignore_list"] = new_ignore_list
        
        try:
            self.config_manager.save_config(self.current_config)
            QMessageBox.information(self, "Success", "Settings saved.")
            signals.config_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")