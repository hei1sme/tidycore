# tidycore/settings_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton, QTreeWidget, QTreeWidgetItem, QMenu,
    QInputDialog, QScrollArea,
    # --- NEW: Add QCheckBox ---
    QCheckBox, QSpinBox, QTabWidget
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from .config_manager import ConfigManager
from .signals import signals
# --- NEW: Import the startup manager instance ---
from .startup_manager import startup_manager
from .utils import isolated_mode, data_root
from pathlib import Path

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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 26, 28, 16)
        main_layout.setSpacing(16)
        title = QLabel('Settings')
        title.setObjectName('Title')
        main_layout.addWidget(title)
        subtitle = QLabel('Choose what moves, and where it belongs.')
        subtitle.setObjectName('Muted')
        main_layout.addWidget(subtitle)
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setAccessibleName('Settings sections')
        general_page = QWidget()
        general_layout = QVBoxLayout(general_page)
        general_layout.setContentsMargins(0, 12, 0, 0)
        general_layout.setSpacing(12)
        general_layout.addWidget(self._create_general_settings_section())
        general_layout.addWidget(self._create_folder_strategy_section())
        note = QLabel('Files wait for a quiet period before moving. Partial downloads and links stay in place. Changing the watched folder starts paused.')
        note.setWordWrap(True)
        note.setObjectName('Caption')
        general_layout.addWidget(note)
        general_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(general_page)
        self.tabs.addTab(scroll, 'General')
        rules_page = QWidget()
        rules_layout = QVBoxLayout(rules_page)
        rules_layout.setContentsMargins(0, 12, 0, 0)
        rules_layout.addWidget(self._create_rules_editor_section())
        self.tabs.addTab(rules_page, 'File type rules')
        ignore_page = QWidget()
        ignore_layout = QVBoxLayout(ignore_page)
        ignore_layout.setContentsMargins(0, 12, 0, 0)
        ignore_layout.addWidget(self._create_ignore_list_section())
        self.tabs.addTab(ignore_page, 'Ignored items')
        main_layout.addWidget(self.tabs, 1)
        footer = QHBoxLayout()
        self.save_feedback = QLabel('Changes apply when you save.')
        self.save_feedback.setWordWrap(True)
        self.save_feedback.setObjectName('Caption')
        footer.addWidget(self.save_feedback, 1)
        self.save_button = QPushButton('Sa&ve settings')
        self.save_button.setObjectName('Primary')
        self.save_button.clicked.connect(self._save_settings)
        footer.addWidget(self.save_button)
        main_layout.addLayout(footer)

    def refresh_settings(self):
        """
        Loads the latest config from disk and populates all UI controls.
        """
        self.current_config = self.config_manager.load_config()
        
        # Populate target folder
        self.folder_path_edit.setText(self.current_config.get("target_folder", ""))
        self.folder_path_edit.setToolTip(self.current_config.get("target_folder", ""))
        self.folder_path_edit.setCursorPosition(0)
        
        self.cooldown_spin.setValue(int(self.current_config.get('cooldown_period_seconds', 5)))

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
        self.folder_path_edit.setToolTip(self.current_config.get("target_folder", ""))
        self.folder_path_edit.setCursorPosition(0)
        self.folder_path_edit.setAccessibleName('Folder to organize')
        self.folder_path_edit.setPlaceholderText('Choose a folder before starting')
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_for_folder)
        target_folder_layout.addWidget(self.folder_path_edit)
        target_folder_layout.addWidget(browse_button)
        
        # Startup checkbox part
        self.startup_checkbox = QCheckBox("Launch TidyCore when computer starts")
        self.startup_checkbox.setEnabled(not isolated_mode())
        if isolated_mode():
            self.startup_checkbox.setToolTip('Startup integration is disabled in isolated test mode.')
        
        layout.addLayout(target_folder_layout)
        cooldown_row = QHBoxLayout()
        cooldown_label = QLabel('&Stability wait (seconds)')
        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(1, 3600)
        self.cooldown_spin.setMaximumWidth(140)
        self.cooldown_spin.setAccessibleName('Stability wait in seconds')
        cooldown_label.setBuddy(self.cooldown_spin)
        cooldown_row.addWidget(cooldown_label)
        cooldown_row.addWidget(self.cooldown_spin)
        cooldown_row.addStretch()
        layout.addLayout(cooldown_row)
        layout.addWidget(self.startup_checkbox)
        
        return box

    def _browse_for_folder(self):
        folder_name = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
        if folder_name:
            self.folder_path_edit.setText(folder_name)

    def _create_folder_strategy_section(self) -> QGroupBox:
        box = QGroupBox("Folder Handling Strategy")
        layout = QVBoxLayout(box)
        layout.setSpacing(10)
        self.smart_scan_radio = QRadioButton("Categorize by folder contents")
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
        box = QGroupBox("File type rules")
        layout = QVBoxLayout(box)

        self.rules_tree = QTreeWidget()
        self.rules_tree.setHeaderLabels(["Category / Extension"])
        self.rules_tree.setAlternatingRowColors(True)
        # Enable the context menu
        self.rules_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.rules_tree.customContextMenuRequested.connect(self._open_rules_context_menu)

        # --- NEW: A single button to add top-level categories ---
        add_category_btn = QPushButton("Add category…")
        add_category_btn.clicked.connect(self._add_top_level_category)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(add_category_btn)

        layout.addWidget(self.rules_tree)
        editor_actions = QHBoxLayout()
        add_ext = QPushButton('Add extension…')
        self.rule_add_extension = add_ext
        add_sub = QPushButton('Add subcategory…')
        self.rule_add_subcategory = add_sub
        remove = QPushButton('Remove')
        self.rule_remove = remove
        add_ext.clicked.connect(lambda: self._add_to_selected(False))
        add_sub.clicked.connect(lambda: self._add_to_selected(True))
        remove.clicked.connect(self._remove_selected_rule)
        for button in (add_ext, add_sub, remove):
            editor_actions.addWidget(button)
        layout.addLayout(editor_actions)
        self.rules_tree.itemSelectionChanged.connect(self._update_rule_actions)
        self._update_rule_actions()
        layout.addLayout(button_layout)
        
        return box

    def _update_rule_actions(self):
        item = self.rules_tree.currentItem()
        category = bool(item and not item.text(0).startswith('.'))
        self.rule_add_extension.setEnabled(category)
        self.rule_add_subcategory.setEnabled(category and item.parent() is None)
        self.rule_remove.setEnabled(item is not None)

    def _add_to_selected(self, subcategory):
        item = self.rules_tree.currentItem()
        if item and not item.text(0).startswith('.') and (not subcategory or item.parent() is None):
            self._add_item(item, is_subcategory=subcategory, is_extension=not subcategory)

    def _remove_selected_rule(self):
        item = self.rules_tree.currentItem()
        if item:
            self._remove_item(item)

    def _open_rules_context_menu(self, position):
        menu = QMenu()
        selected_item = self.rules_tree.currentItem()

        if not selected_item:
            # Right-clicked on an empty area
            add_top_action = QAction("Add category…", self)
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
                
                add_sub_cat_action.setEnabled(selected_item.parent() is None)
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
        self.current_config['target_folder'] = self.folder_path_edit.text()
        self.current_config['cooldown_period_seconds'] = self.cooldown_spin.value()
        self.current_config['start_paused'] = True
        
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
            if category_name.casefold() in {x.casefold() for x in new_rules}:
                self.save_feedback.setText('Category names must be unique.')
                return
            
            # This is the new, robust saving algorithm
            has_sub_categories = False
            flat_extensions = []
            nested_rules = {}
            
            for j in range(category_item.childCount()):
                child_item = category_item.child(j)
                # If a child has its own children, it's a sub-category
                if not child_item.text(0).startswith('.'):
                    has_sub_categories = True
                    sub_name = child_item.text(0)
                    if sub_name.casefold() in {x.casefold() for x in nested_rules}:
                        self.save_feedback.setText('Subcategory names must be unique.')
                        return
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
            if isolated_mode() and self.current_config['target_folder']:
                Path(self.current_config['target_folder']).resolve().relative_to(data_root())
            self.config_manager.save_config(self.current_config)
            startup_error = None
            try:
                if not isolated_mode() and self.startup_checkbox.isChecked() != startup_manager.is_enabled():
                    startup_manager.enable() if self.startup_checkbox.isChecked() else startup_manager.disable()
            except OSError as exc:
                startup_error = str(exc)
            self.save_feedback.setText(
                f'Settings saved, but startup could not be changed: {startup_error}' if startup_error else
                'Settings saved. A changed folder starts paused; use Start watching in Activity.')
            signals.config_changed.emit()
        except Exception as e:
            self.save_feedback.setText(f'Settings could not be fully applied: {e}')
