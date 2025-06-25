# tidycore/folder_decision_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class FolderDecisionWidget(QWidget):
    """A widget representing a single folder move decision."""
    def __init__(self, engine, original_path, new_path, category, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.original_path = original_path
        self.new_path = new_path
        self.folder_name = original_path.split(sep='\\')[-1] # Simple way to get name

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)

        # Main Info Label
        info_text = f"Folder <b>'{self.folder_name}'</b> was categorized as <b>{category}</b>."
        info_label = QLabel(info_text)
        
        # Reason/Path Label
        reason_text = f"Moved to: {new_path}"
        reason_label = QLabel(reason_text)
        reason_label.setStyleSheet("color: #8be9fd;") # Cyan color for path

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.addStretch() # Push buttons to the right
        
        self.undo_button = QPushButton("Undo Move")
        self.ignore_button = QPushButton("Ignore Folder")
        
        self.undo_button.clicked.connect(self._undo_action)
        self.ignore_button.clicked.connect(self._ignore_action)

        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.ignore_button)

        main_layout.addWidget(info_label)
        main_layout.addWidget(reason_label)
        main_layout.addLayout(button_layout)
        
        self.setStyleSheet("""
            FolderDecisionWidget {
                background-color: #3a3c5a;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)

    def _undo_action(self):
        """Handles the Undo button click."""
        # The new destination for the undo is the engine's target folder
        undo_destination = self.engine.target_folder / self.folder_name
        self.engine.undo_move(self.new_path, str(undo_destination))
        # Disable buttons after action is taken
        self.undo_button.setEnabled(False)
        self.undo_button.setText("Undone")

    def _ignore_action(self):
        """Handles the Ignore button click."""
        self.engine.add_to_ignore_list(self.folder_name)
        # Disable button after action
        self.ignore_button.setEnabled(False)
        self.ignore_button.setText("Ignored")