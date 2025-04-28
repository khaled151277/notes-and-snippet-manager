# --- START OF FILE ui/note_editor.py ---

# ui/note_editor.py

from PyQt6.QtWidgets import (
    QVBoxLayout, QTextEdit, QHBoxLayout, QToolBar, QComboBox, QFontComboBox,
    QSpinBox, QColorDialog, QApplication, QStyle, QWidgetAction,
    QDialog, QLineEdit, QDialogButtonBox, QFormLayout, QMessageBox
)
from PyQt6.QtGui import (
    QAction, QIcon, QTextCharFormat, QFont, QKeySequence, QDesktopServices, QTextCursor,
    QMouseEvent, QColor, QTextFormat, QPalette
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QUrl, QSize
from ui.base_editor import BaseEditor, get_icon
from database.models import Note
from database.data_manager import DataManager
from typing import Optional, List, Tuple
from pathlib import Path
import re
import html

LINK_URL_PROPERTY = QTextFormat.Property.UserProperty + 1

class InsertLinkDialog(QDialog):
    def __init__(self, parent=None, selected_text="", existing_url=""):
        super().__init__(parent)
        self.setWindowTitle("Insert/Edit Link")
        self.layout = QFormLayout(self)
        self.text_input = QLineEdit(selected_text)
        self.url_input = QLineEdit(existing_url or "https://")
        self.url_input.setPlaceholderText("Enter URL (e.g., https://example.com or mailto:user@example.com)")
        self.layout.addRow("Display Text:", self.text_input)
        self.layout.addRow("Link URL:", self.url_input)
        self.button_box = QDialogButtonBox()
        self.button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        if existing_url:
            self.remove_button = self.button_box.addButton("Remove Link", QDialogButtonBox.ButtonRole.DestructiveRole)
            self.remove_button.clicked.connect(self.remove_link)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)
        self.link_removed = False

    def remove_link(self):
        self.link_removed = True
        self.accept()

    def get_link_data(self) -> Optional[Tuple[str, str, bool]]:
        if self.exec() == QDialog.DialogCode.Accepted:
            if self.link_removed: return "", "", True
            text = self.text_input.text().strip()
            url = self.url_input.text().strip()
            if not text and url: text = url
            if text and url: return text, url, False
            elif not url: QMessageBox.warning(self,"Input Error", "Link URL is required."); return None
            else: QMessageBox.warning(self,"Input Error", "Display Text and Link URL are required (URL used if text empty)."); return None
        return None


class ClickableTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)

    def get_link_property_at_cursor(self, cursor: QTextCursor) -> Optional[str]:
        char_format = cursor.charFormat()
        url_variant = char_format.property(LINK_URL_PROPERTY)
        if url_variant is not None: return str(url_variant)
        cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, 1)
        char_format_before = cursor.charFormat()
        url_variant_before = char_format_before.property(LINK_URL_PROPERTY)
        if url_variant_before is not None: return str(url_variant_before)
        return None

    def mousePressEvent(self, event: QMouseEvent):
        cursor = self.cursorForPosition(event.pos())
        url_str = self.get_link_property_at_cursor(cursor)
        if url_str: self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else: self.viewport().unsetCursor()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        cursor = self.cursorForPosition(event.pos())
        url_str = self.get_link_property_at_cursor(cursor)
        if url_str: self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        else: self.viewport().unsetCursor()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.viewport().unsetCursor()
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            url_str = self.get_link_property_at_cursor(cursor)
            if not url_str:
                 anchor = self.anchorAt(event.pos())
                 if anchor:
                     print(f"    Found anchor via anchorAt(): {anchor}")
                     if "://" in anchor or "@" in anchor or anchor.startswith("www.") or anchor.startswith("mailto:"): url_str = anchor
                     else: print(f"    Anchor '{anchor}' seems invalid or unsupported.")
                 else: print("--- ClickableTextEdit: No link property or anchor found at release position ---")

            if url_str:
                print(f"--- ClickableTextEdit: Trying to open link: {url_str} ---")
                final_url = QUrl.fromUserInput(url_str)
                if not final_url.scheme():
                    href_string = final_url.toString(QUrl.UrlFormattingOption.RemoveScheme | QUrl.UrlFormattingOption.RemoveUserInfo | QUrl.UrlFormattingOption.RemovePort | QUrl.UrlFormattingOption.RemoveQuery | QUrl.UrlFormattingOption.RemoveFragment).strip('/')
                    print(f"    Re-Checking string from href (no scheme): '{href_string}'")
                    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if re.match(email_regex, href_string): final_url = QUrl(f"mailto:{href_string}")
                    elif href_string.startswith("www.") or "." in href_string:
                         if "://" not in href_string: final_url = QUrl(f"https://{href_string}")
                    else: print(f"    Still cannot determine type for link without scheme: {href_string}"); return

                is_valid = final_url.isValid()
                print(f"    Final URL check: {final_url.toString()}, Scheme: {final_url.scheme() or 'None'}, Valid: {is_valid}")
                if is_valid:
                    print(f"    Attempting to open valid URL with QDesktopServices...")
                    if not QDesktopServices.openUrl(final_url): print(f"    !!! Failed to open URL via QDesktopServices: {final_url.toString()}")
                    else: print(f"    QDesktopServices.openUrl call succeeded.")
                else: print(f"    !!! Final URL is invalid, not attempting to open.")
                event.accept(); return
        super().mouseReleaseEvent(event)

    def apply_link_format(self, text: str, url_str: str):
         cursor = self.textCursor()
         qurl_check = QUrl.fromUserInput(url_str)
         valid_url_str = url_str
         if not qurl_check.scheme() and "@" in url_str: valid_url_str = f"mailto:{url_str}"; qurl_check = QUrl.fromUserInput(valid_url_str)
         elif not qurl_check.scheme() and ("." in url_str or url_str.startswith("www.")):
              if "://" not in url_str: valid_url_str = f"https://{url_str}"; qurl_check = QUrl.fromUserInput(valid_url_str)
         if not qurl_check.isValid():
             print(f"Warning: Cannot apply invalid link URL: {url_str} (Validated as: {valid_url_str})")
             if not cursor.hasSelection(): cursor.insertText(text)
             else: cursor.insertText(cursor.selectedText())
             return
         link_format = QTextCharFormat()
         link_format.setForeground(QApplication.palette().color(QPalette.ColorRole.Link))
         link_format.setFontUnderline(True)
         link_format.setProperty(LINK_URL_PROPERTY, valid_url_str)
         link_format.setToolTip(f"Link: {valid_url_str}")
         if cursor.hasSelection():
             if text != cursor.selectedText(): cursor.insertText(text, link_format)
             else: cursor.mergeCharFormat(link_format)
         else: cursor.insertText(text, link_format)
         self.setCurrentCharFormat(QTextCharFormat())
         self.setTextCursor(cursor)

    def remove_link_format(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
             pos_cursor = QTextCursor(cursor); url_prop = self.get_link_property_at_cursor(pos_cursor)
             if url_prop:
                 cursor.select(QTextCursor.SelectionType.WordUnderCursor)
                 if self.get_link_property_at_cursor(cursor) != url_prop: cursor.clearSelection(); print("Remove Link: Word under cursor doesn't match link property."); return
             else: print("Remove Link: No text selected."); return
        neutral_format = QTextCharFormat()
        neutral_format.setForeground(QApplication.palette().color(QPalette.ColorRole.WindowText))
        neutral_format.setFontUnderline(False)
        neutral_format.clearProperty(LINK_URL_PROPERTY)
        neutral_format.setToolTip("")
        cursor.setCharFormat(neutral_format)
        print(f"Removed link format from selection.")


class NoteEditor(BaseEditor):
    note_saved = pyqtSignal(Note)
    note_deleted = pyqtSignal(int)
    def __init__(self, note_data: Optional[Note] = None, data_manager: DataManager = None):
        super().__init__(editor_type='note', object_data=note_data, data_manager=data_manager)
        self.alignment_actions: List[QAction] = []
    def _setup_specific_editor_ui(self):
        self.content_editor = ClickableTextEdit(self)
        self.format_toolbar = QToolBar("Formatting")
        self.format_toolbar.setFloatable(False); self.format_toolbar.setMovable(False); self.format_toolbar.setIconSize(QSize(18, 18))
        action_bold = QAction(get_icon("bold.png", QStyle.StandardPixmap.SP_DialogYesButton), "Bold", self); action_bold.setToolTip("Bold (Ctrl+B)"); action_bold.setShortcut(QKeySequence("Ctrl+B")); action_bold.setCheckable(True); action_bold.triggered.connect(self._text_bold); self.format_toolbar.addAction(action_bold)
        action_italic = QAction(get_icon("italic.png", QStyle.StandardPixmap.SP_DialogNoButton), "Italic", self); action_italic.setToolTip("Italic (Ctrl+I)"); action_italic.setShortcut(QKeySequence("Ctrl+I")); action_italic.setCheckable(True); action_italic.triggered.connect(self._text_italic); self.format_toolbar.addAction(action_italic)
        action_underline = QAction(get_icon("underline.png", QStyle.StandardPixmap.SP_DialogHelpButton), "Underline", self); action_underline.setToolTip("Underline (Ctrl+U)"); action_underline.setShortcut(QKeySequence("Ctrl+U")); action_underline.setCheckable(True); action_underline.triggered.connect(self._text_underline); self.format_toolbar.addAction(action_underline)
        self.format_toolbar.addSeparator()
        self.alignment_actions = []
        action_align_left = QAction(get_icon("align_left.png", QStyle.StandardPixmap.SP_ToolBarHorizontalExtensionButton), "Align Left", self); action_align_left.setToolTip("Align Left (Ctrl+L)"); action_align_left.setShortcut(QKeySequence("Ctrl+L")); action_align_left.setCheckable(True); action_align_left.triggered.connect(lambda checked, action=action_align_left: self._handle_alignment_change(action, Qt.AlignmentFlag.AlignLeft)); self.format_toolbar.addAction(action_align_left); self.alignment_actions.append(action_align_left)
        action_align_center = QAction(get_icon("align_center.png", QStyle.StandardPixmap.SP_ToolBarVerticalExtensionButton), "Align Center", self); action_align_center.setToolTip("Align Center (Ctrl+E)"); action_align_center.setShortcut(QKeySequence("Ctrl+E")); action_align_center.setCheckable(True); action_align_center.triggered.connect(lambda checked, action=action_align_center: self._handle_alignment_change(action, Qt.AlignmentFlag.AlignHCenter)); self.format_toolbar.addAction(action_align_center); self.alignment_actions.append(action_align_center)
        action_align_right = QAction(get_icon("align_right.png", QStyle.StandardPixmap.SP_FileDialogDetailedView), "Align Right", self); action_align_right.setToolTip("Align Right (Ctrl+R)"); action_align_right.setShortcut(QKeySequence("Ctrl+R")); action_align_right.setCheckable(True); action_align_right.triggered.connect(lambda checked, action=action_align_right: self._handle_alignment_change(action, Qt.AlignmentFlag.AlignRight)); self.format_toolbar.addAction(action_align_right); self.alignment_actions.append(action_align_right)
        self.format_toolbar.addSeparator()
        self.font_combo = QFontComboBox(self); self.font_combo.setToolTip("Font Family"); self.font_combo.setMaximumWidth(150); self.font_combo.currentFontChanged.connect(self._text_font); self.format_toolbar.addWidget(self.font_combo)
        self.font_size_spin = QSpinBox(self); self.font_size_spin.setToolTip("Font Size"); self.font_size_spin.setRange(1, 100); self.font_size_spin.valueChanged.connect(self._text_font_size); default_font_size = QApplication.font().pointSize(); self.font_size_spin.setValue(default_font_size if default_font_size > 0 else 10); self.format_toolbar.addWidget(self.font_size_spin)
        self.format_toolbar.addSeparator()
        action_color = QAction(get_icon("color.png", QStyle.StandardPixmap.SP_DialogApplyButton), "Text Color", self); action_color.setToolTip("Text Color"); action_color.triggered.connect(self._text_color); self.format_toolbar.addAction(action_color)
        self.format_toolbar.addSeparator()
        action_insert_link = QAction(get_icon("links.png", QStyle.StandardPixmap.SP_DesktopIcon), "Insert/Edit Link", self)
        action_insert_link.setToolTip("Insert or Edit Link (Ctrl+K)")
        action_insert_link.setShortcut(QKeySequence("Ctrl+K"))
        action_insert_link.triggered.connect(self._show_insert_link_dialog)
        self.format_toolbar.addAction(action_insert_link)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.addWidget(self.title_input)
        main_layout.addWidget(self.format_toolbar)
        main_layout.addWidget(self.content_editor, 1)
        main_layout.addWidget(self.tags_input)
        main_layout.addLayout(self._controls_layout)
        self.content_editor.textChanged.connect(self._on_editor_text_changed)
        self.content_editor.currentCharFormatChanged.connect(self._update_format_toolbar)
        self.content_editor.cursorPositionChanged.connect(self._update_format_toolbar)
        self._update_format_toolbar()
    def _show_insert_link_dialog(self):
        cursor = self.content_editor.textCursor()
        selected_text = cursor.selectedText()
        existing_url = ""
        # --- Corrected check for existing link ---
        # Check property at cursor start AND potentially before cursor if no selection
        url_prop = self.content_editor.get_link_property_at_cursor(cursor)

        if url_prop:
            existing_url = url_prop
            # Try to get the text associated with this link property span
            if not selected_text: # If nothing selected, try selecting word under cursor
                temp_cursor = QTextCursor(cursor)
                temp_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
                # Only use selected text if the selected word STILL has the same property
                if self.content_editor.get_link_property_at_cursor(temp_cursor) == url_prop:
                     selected_text = temp_cursor.selectedText()
                     print(f"Editing link under cursor: Text='{selected_text}', URL='{existing_url}'")
                else: # Word is not the link text
                     selected_text = "" # Treat as inserting new link at cursor pos
                     print(f"Cursor inside link span (URL: {existing_url}), but no text selected. Inserting new link.")
            else: # Text was already selected
                 print(f"Editing selected link: Text='{selected_text}', URL='{existing_url}'")
        else:
             print(f"No existing link found at cursor. Inserting new link. Selected text: '{selected_text}'")
        # -------------------------------------------

        dialog = InsertLinkDialog(self, selected_text=selected_text, existing_url=existing_url)
        result = dialog.get_link_data()
        if result:
            display_text, url_str, removed_flag = result
            if removed_flag:
                self.content_editor.remove_link_format()
            elif display_text and url_str:
                self.content_editor.apply_link_format(display_text, url_str)
    # --- Load, Get Data, Formatting Slots remain the same ---
    def _load_specific_fields(self):
        if self.object_data and isinstance(self.object_data, Note):
            html_content = self.object_data.content or ""
            print(f"--- Loading HTML From DB (Link properties might be missing for old links) ---")
            self.content_editor.setHtml(html_content)
        else: print("--- Loading a New Note ---"); self.content_editor.clear()
        self._update_format_toolbar()
    def _get_specific_fields_data(self) -> str: return self.content_editor.toHtml()
    def _get_specific_initial_state_data(self) -> str:
        if self.object_data and isinstance(self.object_data, Note): return self.object_data.content or ""
        return self.content_editor.toHtml()
    def _merge_char_format(self, fmt: QTextCharFormat): cursor = self.content_editor.textCursor(); cursor.mergeCharFormat(fmt); self.content_editor.mergeCurrentCharFormat(fmt)
    def _text_bold(self): fmt = QTextCharFormat(); current_weight = self.content_editor.currentCharFormat().fontWeight(); fmt.setFontWeight(QFont.Weight.Normal if current_weight == QFont.Weight.Bold else QFont.Weight.Bold); self._merge_char_format(fmt)
    def _text_italic(self): fmt = QTextCharFormat(); fmt.setFontItalic(not self.content_editor.currentCharFormat().fontItalic()); self._merge_char_format(fmt)
    def _text_underline(self): fmt = QTextCharFormat(); fmt.setFontUnderline(not self.content_editor.currentCharFormat().fontUnderline()); self._merge_char_format(fmt)
    def _text_font(self, font: QFont): fmt = QTextCharFormat(); fmt.setFont(font); self._merge_char_format(fmt)
    def _text_font_size(self, size: int):
        if size > 0: fmt = QTextCharFormat(); fmt.setFontPointSize(float(size)); self._merge_char_format(fmt)

    def _text_color(self):
        current_color = self.content_editor.currentCharFormat().foreground().color()
        color = QColorDialog.getColor(current_color, self)
        # --- Corrected Indentation ---
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._merge_char_format(fmt)
        # ----------------------------

    def _handle_alignment_change(self, triggered_action: QAction, alignment: Qt.AlignmentFlag):
        if self.content_editor.alignment() != alignment:
            self.content_editor.setAlignment(alignment)
            for action in self.alignment_actions:
                if action is not triggered_action and action.isChecked(): action.blockSignals(True); action.setChecked(False); action.blockSignals(False)
        else: triggered_action.blockSignals(True); triggered_action.setChecked(True); triggered_action.blockSignals(False)
        self._update_format_toolbar()
    def _update_format_toolbar(self):
        if not hasattr(self, 'format_toolbar') or not hasattr(self, 'content_editor'): return
        char_format = self.content_editor.currentCharFormat()
        current_alignment = self.content_editor.alignment()
        for action in self.format_toolbar.actions():
            if not action.isSeparator():
                 widget = self.format_toolbar.widgetForAction(action)
                 if widget: widget.setEnabled(True)
                 elif isinstance(action, QAction): action.setEnabled(True)
            if not action.isCheckable(): continue
            action_text = action.toolTip().split('(')[0].strip()
            is_checked = False
            if action_text == "Bold": is_checked = (char_format.fontWeight() == QFont.Weight.Bold)
            elif action_text == "Italic": is_checked = char_format.fontItalic()
            elif action_text == "Underline": is_checked = char_format.fontUnderline()
            elif action_text == "Align Left": is_checked = (current_alignment == Qt.AlignmentFlag.AlignLeft)
            elif action_text == "Align Center": is_checked = (current_alignment == Qt.AlignmentFlag.AlignHCenter)
            elif action_text == "Align Right": is_checked = (current_alignment == Qt.AlignmentFlag.AlignRight)
            if action.isChecked() != is_checked: action.blockSignals(True); action.setChecked(is_checked); action.blockSignals(False)
        try:
            current_font_in_combo = self.font_combo.currentFont(); current_format_font = char_format.font()
            if current_font_in_combo.family() != current_format_font.family(): self.font_combo.blockSignals(True); self.font_combo.setCurrentFont(current_format_font); self.font_combo.blockSignals(False)
        except Exception as e: print(f"Error updating font combo: {e}")
        try:
            point_size = char_format.fontPointSize(); current_spin_value = self.font_size_spin.value(); target_value = int(point_size) if point_size > 0 else self.font_size_spin.minimum()
            if current_spin_value != target_value: self.font_size_spin.blockSignals(True); self.font_size_spin.setValue(target_value); self.font_size_spin.blockSignals(False)
        except Exception as e: print(f"Error updating font size spin: {e}")
    def _is_specific_data_empty(self, specific_data) -> bool:
         return not self.content_editor.toPlainText().strip()

# ui/note_editor.py
# --- END OF FILE ui/note_editor.py ---
