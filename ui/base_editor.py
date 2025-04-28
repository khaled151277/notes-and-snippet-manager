# ui/base_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox,
    QToolBar, QApplication, QStyle, QButtonGroup # Added QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QIcon, QTextCharFormat, QFont, QKeySequence # Added QKeySequence
from database.data_manager import DataManager
from typing import Optional, Any
from pathlib import Path

# Define the path to the icons directory relative to this file's parent's parent
ICONS_DIR = Path(__file__).parent.parent / "icons"

# Helper function to load icons with fallbacks
def get_icon(icon_name: str, fallback_pixmap: Optional[QStyle.StandardPixmap] = None) -> QIcon:
    """Loads an icon from the ICONS_DIR or returns a fallback standard icon."""
    icon_path = ICONS_DIR / icon_name
    if icon_path.exists():
        custom_icon = QIcon(str(icon_path))
        if not custom_icon.isNull():
            return custom_icon
    if fallback_pixmap is not None:
        style = QApplication.style()
        if style: # Ensure style is available
            return style.standardIcon(fallback_pixmap)
    return QIcon() # Return a null icon if no custom icon and no fallback


# Base class for NoteEditor and SnippetEditor
class BaseEditor(QWidget):
    # Signals emitted by the editor to request actions from MainWindow/DataManager
    saveRequested = pyqtSignal(QObject, object) # self (editor), object_data
    deleteRequested = pyqtSignal(QObject, int) # self (editor), object_id

    # Signal to indicate if the editor has unsaved changes
    dirtyChanged = pyqtSignal(bool)

    # Signal emitted after async save operation completes (success or failure)
    saveCompleted = pyqtSignal(QObject, bool) # self (editor), success (True/False)

    def __init__(self, editor_type: str, object_data: Optional[QObject] = None, data_manager: DataManager = None, parent: QWidget = None):
        super().__init__(parent)
        self.editor_type = editor_type
        self.object_data = object_data
        self.is_new = object_data is None
        self.object_id = getattr(object_data, 'id', None)
        self.data_manager = data_manager

        self._is_dirty = False

        # Common UI elements
        self.title_input = QLineEdit()
        self.tags_input = QLineEdit()
        self.save_btn = QPushButton(get_icon("save.png", QStyle.StandardPixmap.SP_DialogSaveButton), "Save")
        self.delete_btn = QPushButton(get_icon("delete.png", QStyle.StandardPixmap.SP_TrashIcon), "Delete")

        # Common controls layout
        self._controls_layout = QHBoxLayout()

        # Store initial state for dirty tracking
        self._initial_title = ""
        self._initial_tags = ""
        self._initial_specific_data = None

        # Setup UI parts
        self._setup_common_ui()
        self._setup_specific_editor_ui() # Implemented by derived class
        self._setup_controls_ui() # Setup layout for common controls (buttons)

        self._connect_signals()

        if not self.is_new:
            self._load_data()
        else:
             self._is_dirty = False
             self.delete_btn.setVisible(False)

        # Capture initial state AFTER loading or setting up new empty editor
        self._initial_title = self.title_input.text()
        self._initial_tags = self.tags_input.text()
        self._initial_specific_data = self._get_specific_initial_state_data()
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}): Initial state captured. Dirty: {self._is_dirty}")

        # Connections from DataManager are handled by MainWindow


    def _setup_common_ui(self):
        """Setup common UI elements (placeholders, tooltips, shortcuts)."""
        if self.editor_type == 'note':
             self.title_input.setPlaceholderText("Note title...")
        elif self.editor_type == 'snippet':
             self.title_input.setPlaceholderText("Snippet title...")
        else:
             self.title_input.setPlaceholderText("Title...")

        self.tags_input.setPlaceholderText("Tags (comma separated)...")

        # Tooltips and Shortcuts for common buttons
        self.save_btn.setToolTip("Save changes (Ctrl+S)")
        self.save_btn.setShortcut(QKeySequence("Ctrl+S"))
        self.delete_btn.setToolTip("Delete this item (Ctrl+Delete)")
        self.delete_btn.setShortcut(QKeySequence("Ctrl+Delete"))


    def _setup_specific_editor_ui(self):
        """Abstract method: Setup UI elements specific to this editor type."""
        # Derived classes must implement this.
        # They should:
        # 1. Create their main layout (e.g., QVBoxLayout(self)).
        # 2. Create and setup their specific widgets (e.g., QTextEdit, QComboBox).
        # 3. Add self.title_input, specific widgets, self.tags_input, and self._controls_layout
        #    to their main layout in the desired order.
        # 4. Connect specific widgets' signals (e.g., textChanged) to self._on_editor_text_changed.
        raise NotImplementedError("Derived classes must implement _setup_specific_editor_ui")

    def _setup_controls_ui(self):
        """Setup common control buttons layout."""
        self._controls_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._controls_layout.setContentsMargins(0, 0, 0, 0)

        # Derived classes can insert specific buttons before these common ones
        # using self._controls_layout.insertWidget(0, ...)

        self._controls_layout.addWidget(self.delete_btn)
        self._controls_layout.addWidget(self.save_btn)

        # Derived class must add self._controls_layout to its main layout


    def _connect_signals(self):
        """Connect common signals."""
        self.save_btn.clicked.connect(self._save_requested)
        self.delete_btn.clicked.connect(self._delete_requested)

        # Connect common input fields to dirty state tracking
        self.title_input.textChanged.connect(self._on_editor_text_changed)
        self.tags_input.textChanged.connect(self._on_editor_text_changed)
        # Specific editor fields (like text editor) must connect in derived class


    def _load_data(self):
        """Load object data into UI fields."""
        if self.object_data:
            self.title_input.setText(getattr(self.object_data, 'title', ''))
            self.tags_input.setText(getattr(self.object_data, 'tags', ''))
            self._load_specific_fields() # Load specific fields in derived class

        self._is_dirty = False


    def _load_specific_fields(self):
        """Abstract method: Load data into specific editor fields."""
        raise NotImplementedError("Derived classes must implement _load_specific_fields")


    def _get_specific_fields_data(self) -> Any:
        """Abstract method: Return data from specific editor fields."""
        raise NotImplementedError("Derived classes must implement _get_specific_fields_data")

    def _get_specific_initial_state_data(self) -> Any:
        """Abstract method: Return initial data from specific editor fields."""
        raise NotImplementedError("Derived classes must implement _get_specific_initial_state_data")


    def _save_requested(self):
        """Handle save button click or save request."""
        title = self.title_input.text().strip()
        tags = self.tags_input.text().strip()
        specific_data = self._get_specific_fields_data()

        specific_data_is_empty = self._is_specific_data_empty(specific_data)

        if not title and specific_data_is_empty:
            print(f"Cannot save empty item ({'New' if self.is_new else self.object_id}). Title and content/code are empty.")
            QMessageBox.warning(self, "Cannot Save", "Please enter a title or content/code before saving.")
            self.saveCompleted.emit(self, False)
            return

        save_data = {
            'id': self.object_id,
            'title': title,
            'tags': tags,
            'specific_data': specific_data,
            'is_new': self.is_new,
            'editor_type': self.editor_type
        }
        self.saveRequested.emit(self, save_data)


    def _delete_requested(self):
        """Handle delete button click or delete request."""
        if self.is_new or self.object_id is None:
             print("Cannot delete unsaved or new item.")
             return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{self.title_input.text().strip()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.deleteRequested.emit(self, self.object_id)


    def _on_editor_text_changed(self):
        """Slot connected to text/value changes in editor fields."""
        self._update_dirty_state()


    def _update_dirty_state(self):
        """Recalculate dirty state and emit signal if changed."""
        current_title = self.title_input.text()
        current_tags = self.tags_input.text()
        current_specific_data = self._get_specific_fields_data()

        is_currently_dirty = (current_title != self._initial_title or
                              current_tags != self._initial_tags or
                              current_specific_data != self._initial_specific_data)

        if is_currently_dirty != self._is_dirty:
            self._is_dirty = is_currently_dirty
            print(f"Editor {self.object_id or 'New'} ({self.editor_type}): Dirty state changed -> {self._is_dirty}")
            self.dirtyChanged.emit(self._is_dirty)


    def _is_specific_data_empty(self, specific_data) -> bool:
        """Checks if the specific data from the editor fields is considered empty."""
        # Default implementation checks for None, empty string, or tuple of empty strings
        return (specific_data is None or
                (isinstance(specific_data, str) and not specific_data.strip()) or
                (isinstance(specific_data, tuple) and all(not item.strip() for item in specific_data if isinstance(item, str)))
               )


    def handle_save_success(self, saved_object):
        """Called by MainWindow when async save completes successfully."""
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}) received save success for ID: {getattr(saved_object, 'id', 'N/A')}.")
        # Update internal state
        self.object_data = saved_object
        self.is_new = False
        self.object_id = getattr(saved_object, 'id', None)
        self.delete_btn.setVisible(True)

        # Update initial state to match the newly saved state
        self._initial_title = self.title_input.text()
        self._initial_tags = self.tags_input.text()
        self._initial_specific_data = self._get_specific_fields_data() # Re-capture current state as initial

        # Recalculate dirty state (should become False)
        self._update_dirty_state()

        # Emit specific saved signal for MainWindow UI updates
        if self.editor_type == 'note':
            if hasattr(self, 'note_saved'):
                self.note_saved.emit(saved_object)
        elif self.editor_type == 'snippet':
            if hasattr(self, 'snippet_saved'):
                 self.snippet_saved.emit(saved_object)

        self.saveCompleted.emit(self, True)


    def handle_delete_success(self):
        """Called by MainWindow when async delete completes successfully."""
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}) received delete success.")
        # Emit specific deleted signal for MainWindow UI updates
        if self.editor_type == 'note':
            if hasattr(self, 'note_deleted'):
                 self.note_deleted.emit(self.object_id)
        elif self.editor_type == 'snippet':
            if hasattr(self, 'snippet_deleted'):
                 self.snippet_deleted.emit(self.object_id)
        # MainWindow handles tab closure


    def handle_db_error(self, error_message: str):
        """Called by MainWindow when an async DB operation for this editor fails."""
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}) received DB error: {error_message}")
        QMessageBox.critical(self, f"{self.editor_type.capitalize()} Database Error", f"An error occurred:\n{error_message}")

        # Emit saveCompleted(False) assuming the error relates to a pending save
        # A more robust solution would track task IDs.
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}): Emitting saveCompleted(False) due to DB error.")
        self.saveCompleted.emit(self, False)


    # Public methods used by MainWindow
    def is_dirty(self) -> bool:
        """Returns True if the editor has unsaved changes."""
        # Ensure dirty state is up-to-date before returning
        self._update_dirty_state()
        return self._is_dirty

    def save_changes(self):
        """Requests to save changes if dirty. Called by MainWindow during tab close."""
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}) requesting save via save_changes.")
        self._save_requested() # Triggers save process (checks dirty, validates)


    def get_object_id(self) -> Optional[int]:
        """Returns the ID of the object being edited."""
        return self.object_id

# ui/base_editor.py
# --- END OF FILE base_editor.py ---
