# --- START OF FILE widgets/snippet_item.py ---

# widgets/snippet_item.py
from PyQt6.QtWidgets import QListWidgetItem, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from database.models import Snippet

class SnippetItemWidget(QWidget):
    """Custom widget for displaying snippet details in QListWidget."""
    def __init__(self, snippet: Snippet):
        super().__init__()
        self.snippet_data = snippet
        self.setObjectName("SnippetItemWidget")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 3, 5, 3)
        layout.setSpacing(2)

        self.title_label = QLabel() # Set text later
        self.title_label.setObjectName("title_label")
        title_font = self.title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self.title_label.setFont(title_font)
        self.title_label.setWordWrap(False)

        self.detail_layout = QHBoxLayout()
        self.detail_layout.setSpacing(6)

        self.lang_label = QLabel()
        self.lang_label.setObjectName("lang_label")
        self.tags_label = QLabel()
        self.tags_label.setObjectName("tags_label")
        self.date_label = QLabel()
        self.date_label.setObjectName("date_label")

        detail_font = self.date_label.font()
        detail_font_size = title_font.pointSize() - 2 if title_font.pointSize() > 8 else 8
        detail_font.setPointSize(detail_font_size)
        self.lang_label.setFont(detail_font)
        self.tags_label.setFont(detail_font)
        self.date_label.setFont(detail_font)

        self.lang_label.setStyleSheet("color: #aaa;")
        self.tags_label.setStyleSheet("color: #aaa;")
        self.date_label.setStyleSheet("color: #aaa;")

        self.detail_layout.addWidget(self.lang_label)
        self.detail_layout.addWidget(self.tags_label)
        self.detail_layout.addStretch(1)
        self.detail_layout.addWidget(self.date_label)

        layout.addWidget(self.title_label)
        layout.addLayout(self.detail_layout)

        self.update_display() # Call after creating all labels

    def update_display(self):
        """Updates the labels with current snippet_data. Checks widget validity."""
        if not self.title_label or not self.lang_label or not self.tags_label or not self.date_label:
            print(f"Warning: Attempting to update display of potentially deleted SnippetItemWidget for Snippet ID: {self.snippet_data.id if self.snippet_data else 'N/A'}")
            return

        try:
            self.title_label.setText(self.snippet_data.title or "Untitled Snippet")

            lang_text = f"Lang: {self.snippet_data.language or 'N/A'}"
            self.lang_label.setText(lang_text)

            tags_text = f"Tags: {self.snippet_data.tags}" if self.snippet_data.tags else ""
            self.tags_label.setText(tags_text)
            self.tags_label.setVisible(bool(self.snippet_data.tags))

            # --- Format date correctly ---
            date_obj = self.snippet_data.created_at # Use created_at for snippets
            date_str = date_obj.strftime("%Y-%m-%d %H:%M") if date_obj else "No date"
            # -----------------------------
            self.date_label.setText(date_str)

            tooltip_parts = [
                f"Title: {self.snippet_data.title or 'N/A'}",
                f"Language: {self.snippet_data.language or 'N/A'}",
                f"Tags: {self.snippet_data.tags or 'None'}",
                f"Created: {self.snippet_data.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.snippet_data.created_at else 'N/A'}"
            ]
            self.setToolTip("\n".join(tooltip_parts))
        except RuntimeError as e:
             print(f"RuntimeError during update_display for Snippet ID {self.snippet_data.id if self.snippet_data else 'N/A'}: {e}")


class SnippetItem(QListWidgetItem):
    """QListWidgetItem wrapper for a Snippet, using a custom widget."""
    def __init__(self, snippet: Snippet):
        super().__init__()
        self.data_object = snippet
        self.widget = SnippetItemWidget(snippet)
        self.setSizeHint(self.widget.sizeHint())

    def update_data(self, snippet: Snippet):
        """Updates the item's data and refreshes the display widget."""
        self.data_object = snippet
        if self.widget:
            try:
                self.widget.snippet_data = snippet
                self.widget.update_display()
                self.setSizeHint(self.widget.sizeHint())
            except RuntimeError as e:
                print(f"RuntimeError during SnippetItem update_data for Snippet ID {snippet.id}: {e}. Widget might be deleting.")
        else:
            print(f"Warning: Cannot update data for SnippetItem {snippet.id}, widget is None.")


# widgets/snippet_item.py
# --- END OF FILE snippet_item.py ---