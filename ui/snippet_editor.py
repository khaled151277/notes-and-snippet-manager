# --- START OF FILE snippet_editor.py ---

# ui/snippet_editor.py

from PyQt6.QtWidgets import (
    QVBoxLayout, QTextEdit, QComboBox, QHBoxLayout, QPushButton, QMessageBox,
    QApplication, QStyle # Added QApplication, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
# --- Added QFont import ---
from PyQt6.QtGui import QKeySequence, QIcon, QFont
# --------------------------
from ui.base_editor import BaseEditor, get_icon # Import base class and icon helper
from .syntax_highlighter import SyntaxHighlighter
from database.models import Snippet
from database.data_manager import DataManager
from typing import Optional, Tuple

class SnippetEditor(BaseEditor):
    # Specific signals for snippets (emitted by base class handlers)
    snippet_saved = pyqtSignal(Snippet)
    snippet_deleted = pyqtSignal(int)

    def __init__(self, snippet_data: Optional[Snippet] = None, data_manager: DataManager = None):
        # Pass 'snippet' editor_type and data to the base class.
        super().__init__(editor_type='snippet', object_data=snippet_data, data_manager=data_manager)
        # Specific widgets are created in _setup_specific_editor_ui

    def _setup_specific_editor_ui(self):
        """Implement abstract method: Setup UI elements specific to SnippetEditor."""
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Python", "JavaScript", "HTML", "CSS", "SQL", "Java", "C++", "C#", "PHP", "Ruby", "Go", "Text"]) # Added more languages + Text
        self.language_combo.setToolTip("Select programming language for syntax highlighting")

        self.code_editor = QTextEdit()
        # Improve font for code
        font = QFont("Courier New", 11) # Or another monospace font like 'Consolas', 'Monaco', 'Source Code Pro'
        # Check if the font is actually available, otherwise default font will be used
        # from PyQt6.QtGui import QFontDatabase
        # if QFontDatabase.hasFamily("Courier New"):
        #     font = QFont("Courier New", 11)
        # else:
        #     font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont) # Use system fixed-width font
        #     font.setPointSize(11)

        self.code_editor.setFont(font)
        # Optionally disable rich text features if only plain code is desired
        self.code_editor.setAcceptRichText(False)
        # Set tab stop distance (e.g., 4 spaces)
        self.code_editor.setTabStopDistance(font.pointSize() * 4)


        # Setup Syntax Highlighting
        self.highlighter = SyntaxHighlighter(self.code_editor.document(), self.language_combo.currentText())
        self.language_combo.currentTextChanged.connect(self.highlighter.set_language)

        # --- Copy Code Button ---
        self.copy_btn = QPushButton(get_icon("copy.png", QStyle.StandardPixmap.SP_DialogSaveButton), "Copy Code") # Used Save as fallback
        self.copy_btn.setToolTip("Copy code to clipboard (Ctrl+Shift+C)")
        self.copy_btn.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.copy_btn.clicked.connect(self._copy_code_to_clipboard)
        # Insert copy button at the beginning of the common controls layout
        self._controls_layout.insertWidget(0, self.copy_btn)
        # -----------------------

        # --- Layout setup ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # Add common widgets and specific widgets
        main_layout.addWidget(self.title_input)
        main_layout.addWidget(self.language_combo)
        main_layout.addWidget(self.code_editor, 1) # Give editor stretch factor
        main_layout.addWidget(self.tags_input)
        main_layout.addLayout(self._controls_layout) # Add common controls layout

        # Connect specific editor signals for dirty tracking
        self.code_editor.textChanged.connect(self._on_editor_text_changed)
        self.language_combo.currentTextChanged.connect(self._on_editor_text_changed)


    def _load_specific_fields(self):
        """Implement abstract method: Load data into specific SnippetEditor fields."""
        if self.object_data and isinstance(self.object_data, Snippet):
            self.code_editor.setPlainText(self.object_data.code or "") # Ensure code is not None
            language = self.object_data.language or "Text" # Default to Text if null
            index = self.language_combo.findText(language, Qt.MatchFlag.MatchFixedString)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
            else:
                 # If language not in list, select "Text" or "Other"
                 index = self.language_combo.findText("Text", Qt.MatchFlag.MatchFixedString)
                 if index >= 0:
                     self.language_combo.setCurrentIndex(index)

            # Update highlighter language explicitly after loading
            self.highlighter.set_language(self.language_combo.currentText())


    def _get_specific_fields_data(self) -> Tuple[str, str]:
        """Implement abstract method: Return data from specific SnippetEditor fields."""
        return (self.code_editor.toPlainText(), self.language_combo.currentText())

    def _get_specific_initial_state_data(self) -> Tuple[str, str]:
        """Implement abstract method: Return initial data from specific SnippetEditor fields."""
         # Called after initial load or setup
        if self.object_data and isinstance(self.object_data, Snippet):
             return (self.object_data.code or "", self.object_data.language or "Text") # Initial DB state
        # For new snippets
        return (self.code_editor.toPlainText(), self.language_combo.currentText())


    def _copy_code_to_clipboard(self):
        """Copies the content of the code editor to the system clipboard."""
        clipboard = QApplication.clipboard()
        if clipboard:
             code = self.code_editor.toPlainText()
             clipboard.setText(code)
             print(f"Copied {len(code)} characters to clipboard.") # Feedback
             # Optionally show a brief status message in status bar if available
             # Accessing main window's status bar requires passing a reference or using signals
             # For simplicity, just print for now.
             # Alternative: emit a signal that MainWindow connects to show status.
        else:
             print("Error: Could not access clipboard.")


    def _is_specific_data_empty(self, specific_data) -> bool:
         """Checks if the snippet code is empty."""
         # specific_data is a tuple (code, language)
         code, _ = specific_data
         return not code.strip()

# ui/snippet_editor.py
# --- END OF FILE snippet_editor.py ---
