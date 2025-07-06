# tidycore/folder_decision_widget.py
import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class FolderDecisionWidget(QWidget):
    """A widget representing a single folder move decision."""
    def __init__(self, engine, original_path, new_path, category, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.original_path = original_path
        self.new_path = new_path
        self.folder_name = os.path.basename(original_path)

        # Main container styling
        self.setObjectName("DecisionCard")
        self.setStyleSheet("""
            #DecisionCard {
                background-color: rgba(58, 62, 102, 0.85);
                border-radius: 12px;
                margin-bottom: 12px;
                border: 1.5px solid #7aa2f7;
            }
            #DecisionCard QLabel { font-size: 13px; color: #c0c5ea; }
            #DecisionCard QPushButton { 
                font-size: 12px; 
                padding: 6px 14px; 
                font-weight: 500;
                background-color: #7aa2f7;
                color: #23243a;
                border-radius: 8px;
                border: none;
                margin-left: 6px;
                margin-right: 6px;
            }
            #DecisionCard QPushButton:hover { background-color: #bb9af7; color: #fff; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)

        info_text = f"Folder <b>'{self.folder_name}'</b> was categorized as <b>{category}</b>."
        info_label = QLabel(info_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.undo_button = QPushButton("Undo Move")
        self.ignore_button = QPushButton("Always Ignore This Folder")
        
        self.undo_button.clicked.connect(self._undo_action)
        self.ignore_button.clicked.connect(self._ignore_action)

        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.ignore_button)

        main_layout.addWidget(info_label)
        main_layout.addLayout(button_layout)

    def _undo_action(self):
        # The destination for the undo is the original path
        self.engine.undo_move(self.new_path, self.original_path)
        self.undo_button.setEnabled(False)
        self.undo_button.setText("Undone")
        self.ignore_button.hide()

    def _ignore_action(self):
        self.engine.add_to_ignore_list(self.folder_name)
        self.ignore_button.setEnabled(False)
        self.ignore_button.setText("Will be ignored")
        self.undo_button.hide()