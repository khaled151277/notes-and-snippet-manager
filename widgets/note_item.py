# --- START OF FILE note_item.py ---

# widgets/note_item.py
from PyQt6.QtWidgets import QListWidgetItem, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
# --- Import QFont ---
from PyQt6.QtGui import QFont
# --------------------
from database.models import Note

class NoteItemWidget(QWidget):
    """Custom widget for displaying note details in QListWidget."""
    def __init__(self, note: Note):
        super().__init__()
        self.note_data = note
        self.setObjectName("NoteItemWidget") # Keep for potential future styling

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(2)

        self.title_label = QLabel(self.note_data.title or "Untitled Note")
        self.title_label.setObjectName("title_label")
        # --- Set font directly here ---
        title_font = self.title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(12) # Set desired size directly
        self.title_label.setFont(title_font)
        # ------------------------------
        self.title_label.setWordWrap(False)

        self.detail_layout = QHBoxLayout()
        self.detail_layout.setSpacing(6)

        self.tags_label = QLabel()
        self.tags_label.setObjectName("tags_label")
        self.date_label = QLabel()
        self.date_label.setObjectName("date_label")

        # --- Set detail font directly ---
        detail_font = self.date_label.font()
        detail_font_size = title_font.pointSize() - 2 if title_font.pointSize() > 8 else 8 # e.g., 10
        detail_font.setPointSize(detail_font_size)
        self.date_label.setFont(detail_font)
        self.tags_label.setFont(detail_font)
        # --------------------------------

        # --- Set detail color directly (Stylesheet might override, but good practice) ---
        self.tags_label.setStyleSheet("color: #aaa;")
        self.date_label.setStyleSheet("color: #aaa;")
        # ------------------------------------------------------------------------------

        self.detail_layout.addWidget(self.tags_label)
        self.detail_layout.addStretch(1)
        self.detail_layout.addWidget(self.date_label)

        layout.addWidget(self.title_label)
        layout.addLayout(self.detail_layout)

        self.update_display()

    def update_display(self):
        """Updates the labels with current note_data. Checks widget validity."""
        if not self.title_label or not self.tags_label or not self.date_label:
             print(f"Warning: Attempting to update display of potentially deleted NoteItemWidget for Note ID: {self.note_data.id if self.note_data else 'N/A'}")
             return

        try:
            self.title_label.setText(self.note_data.title or "Untitled Note")

            tags_text = f"Tags: {self.note_data.tags}" if self.note_data.tags else ""
            self.tags_label.setText(tags_text)
            self.tags_label.setVisible(bool(self.note_data.tags))

            date_str = self.note_data.updated_at.strftime("%Y-%m-%d %H:%M") if self.note_data.updated_at else "No date"
            self.date_label.setText(date_str)

            tooltip_parts = [
                f"Title: {self.note_data.title or 'N/A'}",
                f"Tags: {self.note_data.tags or 'None'}",
                f"Created: {self.note_data.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.note_data.created_at else 'N/A'}",
                f"Updated: {self.note_data.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.note_data.updated_at else 'N/A'}"
            ]
            self.setToolTip("\n".join(tooltip_parts))
        except RuntimeError as e:
             print(f"RuntimeError during update_display for Note ID {self.note_data.id if self.note_data else 'N/A'}: {e}")


class NoteItem(QListWidgetItem):
    """QListWidgetItem wrapper for a Note, using a custom widget."""
    def __init__(self, note: Note):
        super().__init__()
        self.data_object = note
        self.widget = NoteItemWidget(note)
        self.setSizeHint(self.widget.sizeHint())

    def update_data(self, note: Note):
        """Updates the item's data and refreshes the display widget."""
        self.data_object = note
        if self.widget:
            try:
                self.widget.note_data = note
                self.widget.update_display()
                self.setSizeHint(self.widget.sizeHint())
            except RuntimeError as e:
                 print(f"RuntimeError during NoteItem update_data for Note ID {note.id}: {e}. Widget might be deleting.")
        else:
            print(f"Warning: Cannot update data for NoteItem {note.id}, widget is None.")


# widgets/note_item.py
# --- END OF FILE note_item.py ---
