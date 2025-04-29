# --- START OF FILE ui/base_editor.py ---

# ui/base_editor.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox,
    QToolBar, QApplication, QStyle
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QUrl
# --- Import QDesktopServices ---
from PyQt6.QtGui import QAction, QIcon, QTextCharFormat, QFont, QKeySequence, QDesktopServices, QPalette
# -------------------------------
from database.data_manager import DataManager
from typing import Optional, Any, Dict
from pathlib import Path

ICONS_DIR = Path(__file__).parent.parent / "icons"

def get_icon(icon_name: str, fallback_pixmap: Optional[QStyle.StandardPixmap] = None) -> QIcon:
    icon_path = ICONS_DIR / icon_name
    if icon_path.exists():
        custom_icon = QIcon(str(icon_path))
        if not custom_icon.isNull(): return custom_icon
    if fallback_pixmap is not None:
        style = QApplication.style()
        if style: return style.standardIcon(fallback_pixmap)
    return QIcon()

class BaseEditor(QWidget):
    saveRequested = pyqtSignal(QObject, object)
    deleteRequested = pyqtSignal(QObject, int)
    dirtyChanged = pyqtSignal(bool)
    saveCompleted = pyqtSignal(QObject, bool)

    def __init__(self, editor_type: str, object_data: Optional[QObject] = None, data_manager: DataManager = None, parent: QWidget = None, **kwargs):
        super().__init__(parent)
        self.editor_type = editor_type
        self.object_data = object_data
        self.is_new = object_data is None
        self.object_id = getattr(object_data, 'id', None)
        self.data_manager = data_manager
        self._is_dirty = False
        self.title_input = QLineEdit()
        self.tags_input = QLineEdit()
        self.save_btn = QPushButton(get_icon("save.png", QStyle.StandardPixmap.SP_DialogSaveButton), "Save")
        self.delete_btn = QPushButton(get_icon("delete.png", QStyle.StandardPixmap.SP_TrashIcon), "Delete")
        # --- Add Donate button ---
        self.donate_btn = QPushButton(get_icon("donate.png", QStyle.StandardPixmap.SP_DialogApplyButton), "Donate")
        # -------------------------
        self._controls_layout = QHBoxLayout()
        self._initial_title = ""
        self._initial_tags = ""
        self._initial_specific_data = None

        self._setup_common_ui()
        self._setup_specific_editor_ui()
        self._setup_controls_ui()
        self._connect_signals() # Connect donate button signal here

        if not self.is_new:
            self._load_data()
        else:
             self._is_dirty = False
             self.delete_btn.setVisible(False)

        self._initial_title = self.title_input.text()
        self._initial_tags = self.tags_input.text()
        self._initial_specific_data = self._get_specific_initial_state_data()
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}): Initial state captured. Dirty: {self._is_dirty}")


    def _setup_common_ui(self):
        if self.editor_type == 'note':
            self.title_input.setPlaceholderText("Note title...")
        elif self.editor_type == 'snippet':
            self.title_input.setPlaceholderText("Snippet title...")
        else:
            self.title_input.setPlaceholderText("Title...")
        self.tags_input.setPlaceholderText("Tags (comma separated)...")
        self.save_btn.setToolTip("Save changes (Ctrl+S)")
        self.save_btn.setShortcut(QKeySequence("Ctrl+S"))
        self.delete_btn.setToolTip("Delete this item (Ctrl+Delete)")
        self.delete_btn.setShortcut(QKeySequence("Ctrl+Delete"))
        # --- Tooltip for Donate button ---
        self.donate_btn.setToolTip("If you found the program useful, please support us with a donation")
        # ---------------------------------

    def _setup_specific_editor_ui(self):
        raise NotImplementedError("Derived classes must implement _setup_specific_editor_ui")

    def _setup_controls_ui(self):
        self._controls_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._controls_layout.setContentsMargins(0, 0, 0, 0)
        # Add Donate button next to delete/save
        self._controls_layout.addWidget(self.donate_btn)
        self._controls_layout.addWidget(self.delete_btn)
        self._controls_layout.addWidget(self.save_btn)

    # --- Slot for Donate Button ---
    def _open_donate_link(self):
        # Re-use the same function as in MainWindow for consistency
        url = QUrl("https://www.paypal.com/paypalme/kh1512")
        print(f"Opening donate link from editor: {url.toString()}")
        if not QDesktopServices.openUrl(url):
             QMessageBox.warning(self, "Error", "Could not open donation link in browser.")
    # ----------------------------

    def _connect_signals(self):
        self.save_btn.clicked.connect(self._save_requested)
        self.delete_btn.clicked.connect(self._delete_requested)
        self.title_input.textChanged.connect(self._on_editor_text_changed)
        self.tags_input.textChanged.connect(self._on_editor_text_changed)
        # --- Connect Donate button signal ---
        self.donate_btn.clicked.connect(self._open_donate_link)
        # ----------------------------------

    def _load_data(self):
        if self.object_data:
            self.title_input.setText(getattr(self.object_data, 'title', ''))
            self.tags_input.setText(getattr(self.object_data, 'tags', ''))
            self._load_specific_fields()
        self._is_dirty = False

    def _load_specific_fields(self): raise NotImplementedError
    def _get_specific_fields_data(self) -> Any: raise NotImplementedError
    def _get_specific_initial_state_data(self) -> Any: raise NotImplementedError

    def _save_requested(self):
        title = self.title_input.text().strip()
        tags = self.tags_input.text().strip()
        specific_data = self._get_specific_fields_data()
        specific_data_is_empty = self._is_specific_data_empty(specific_data)
        if not title and specific_data_is_empty:
            QMessageBox.warning(self, "Cannot Save", "Please enter a title or content/code before saving.")
            self.saveCompleted.emit(self, False)
            return
        save_data = {'id': self.object_id, 'title': title, 'tags': tags, 'specific_data': specific_data, 'is_new': self.is_new, 'editor_type': self.editor_type}
        self.saveRequested.emit(self, save_data)

    def _delete_requested(self):
        if self.is_new or self.object_id is None: return
        reply = QMessageBox.question( self, "Confirm Delete", f"Are you sure you want to delete '{self.title_input.text().strip()}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No )
        if reply == QMessageBox.StandardButton.Yes: self.deleteRequested.emit(self, self.object_id)

    def _on_editor_text_changed(self): self._update_dirty_state()

    def _update_dirty_state(self):
        current_title = self.title_input.text()
        current_tags = self.tags_input.text()
        current_specific_data = self._get_specific_fields_data()
        is_currently_dirty = (current_title != self._initial_title or current_tags != self._initial_tags or current_specific_data != self._initial_specific_data)
        if is_currently_dirty != self._is_dirty:
            self._is_dirty = is_currently_dirty
            print(f"Editor {self.object_id or 'New'} ({self.editor_type}): Dirty state changed -> {self._is_dirty}")
            self.dirtyChanged.emit(self._is_dirty)

    def _is_specific_data_empty(self, specific_data) -> bool:
        return (specific_data is None or (isinstance(specific_data, str) and not specific_data.strip()) or (isinstance(specific_data, tuple) and all(not item.strip() for item in specific_data if isinstance(item, str))))

    def handle_save_success(self, saved_object):
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}) received save success for ID: {getattr(saved_object, 'id', 'N/A')}.")
        self.object_data = saved_object; self.is_new = False; self.object_id = getattr(saved_object, 'id', None); self.delete_btn.setVisible(True)
        self._initial_title = self.title_input.text(); self._initial_tags = self.tags_input.text(); self._initial_specific_data = self._get_specific_fields_data()
        self._update_dirty_state()
        if self.editor_type == 'note':
            if hasattr(self, 'note_saved'): self.note_saved.emit(saved_object)
        elif self.editor_type == 'snippet':
            if hasattr(self, 'snippet_saved'): self.snippet_saved.emit(saved_object)
        self.saveCompleted.emit(self, True)

    def handle_delete_success(self):
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}) received delete success.")
        if self.editor_type == 'note':
            if hasattr(self, 'note_deleted'): self.note_deleted.emit(self.object_id)
        elif self.editor_type == 'snippet':
            if hasattr(self, 'snippet_deleted'): self.snippet_deleted.emit(self.object_id)

    def handle_db_error(self, error_message: str):
        print(f"Editor {self.object_id or 'New'} ({self.editor_type}) received DB error: {error_message}")
        QMessageBox.critical(self, f"{self.editor_type.capitalize()} Database Error", f"An error occurred:\n{error_message}")
        self.saveCompleted.emit(self, False)

    def is_dirty(self) -> bool: self._update_dirty_state(); return self._is_dirty
    def save_changes(self): print(f"Editor {self.object_id or 'New'} ({self.editor_type}) requesting save via save_changes."); self._save_requested()
    def get_object_id(self) -> Optional[int]: return self.object_id

# ui/base_editor.py
# --- END OF FILE ui/base_editor.py ---