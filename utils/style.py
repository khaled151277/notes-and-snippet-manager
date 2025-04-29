# --- START OF FILE utils/style.py ---

# utils/style.py
from PyQt6.QtGui import QColor, QPalette, QIcon
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtWidgets import QStyle, QApplication
from pathlib import Path
from typing import Optional

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

def load_styles(app: QApplication, theme_name: str = "dark"):
    theme_name = theme_name.lower()
    print(f"[style.py] load_styles called with theme_name: '{theme_name}'")
    if theme_name == "dark":
        load_dark_theme(app)
    elif theme_name == "light":
        load_light_theme(app)
    else:
        print(f"Warning: Theme '{theme_name}' not recognized. Using default Light theme.")
        load_light_theme(app)

def load_dark_theme(app: QApplication):
    print("[style.py] Loading DARK theme...")
    app.setStyle("Fusion")
    palette = QPalette()
    dark_grey = QColor(53, 53, 53); grey = QColor(75, 75, 75); light_grey = QColor(90, 90, 90); black = QColor(35, 35, 35); white = QColor(240, 240, 240); blue = QColor(42, 130, 218); dark_blue = QColor(30, 100, 180); link_color = QColor(90, 170, 255); visited_color = QColor(180, 140, 255)
    palette.setColor(QPalette.ColorRole.Window, dark_grey); palette.setColor(QPalette.ColorRole.WindowText, white); palette.setColor(QPalette.ColorRole.Base, black); palette.setColor(QPalette.ColorRole.AlternateBase, dark_grey); palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25)); palette.setColor(QPalette.ColorRole.ToolTipText, white); palette.setColor(QPalette.ColorRole.Text, white); palette.setColor(QPalette.ColorRole.Button, dark_grey); palette.setColor(QPalette.ColorRole.ButtonText, white); palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red); palette.setColor(QPalette.ColorRole.Highlight, blue); palette.setColor(QPalette.ColorRole.HighlightedText, black); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, grey); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, grey); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, grey); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, grey);
    palette.setColor(QPalette.ColorRole.Link, link_color); palette.setColor(QPalette.ColorRole.LinkVisited, visited_color)
    app.setPalette(palette)
    print("[style.py] Dark palette set.")
    style_sheet = f"""
        QToolTip {{ color: {white.name()}; background-color: {blue.name()}; border: 1px solid {white.name()}; padding: 4px; opacity: 220; }}
        QMainWindow {{ background-color: {dark_grey.name()}; }}
        QWidget {{ color: {white.name()}; }}
        QGroupBox {{ border: 1px solid {grey.name()}; margin-top: 10px; padding-top: 5px; border-radius: 3px; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; left: 7px; }}
        QTabWidget::pane {{ border: 1px solid {grey.name()}; top: -1px; background-color: {dark_grey.name()}; }}
        QTabWidget::tab-bar {{ left: 5px; }}
        QTabBar::tab {{ background: {dark_grey.name()}; color: {white.name()}; border: 1px solid {grey.name()}; border-bottom-color: {grey.name()}; border-top-left-radius: 4px; border-top-right-radius: 4px; min-width: 8ex; padding: 5px 10px; margin-right: 2px; padding-right: 25px; }}
        QTabBar::tab:selected {{ background: {blue.name()}; color: {black.name()}; border-color: {blue.name()}; border-bottom-color: {blue.name()}; }}
        QTabBar::tab:!selected:hover {{ background: {light_grey.name()}; }}
        QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser {{ background-color: {black.name()}; color: {white.name()}; border: 1px solid {grey.name()}; border-radius: 3px; padding: 4px; selection-background-color: {blue.name()}; selection-color: {black.name()}; }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus {{ border: 1px solid {blue.name()}; }}
        QTextEdit a {{ color: palette(link); text-decoration: underline; }}
        QPushButton {{ background-color: {dark_grey.name()}; color: {white.name()}; border: 1px solid {grey.name()}; padding: 5px 10px; border-radius: 3px; min-width: 70px; }}
        QPushButton:hover {{ background-color: {light_grey.name()}; border: 1px solid {blue.name()}; }}
        QPushButton:pressed {{ background-color: {dark_blue.name()}; }}
        QPushButton:disabled {{ background-color: {grey.name()}; color: {light_grey.name()}; border-color: {dark_grey.name()}; }}
        QListWidget {{ background-color: {black.name()}; border: 1px solid {grey.name()}; border-radius: 3px; padding: 2px; outline: 0; }}
        QListWidget::item {{ border-radius: 0px; padding: 1px 0px; }}
        NoteItemWidget QLabel#title_label, SnippetItemWidget QLabel#title_label {{ font-weight: bold; color: {white.name()}; background-color: transparent; }}
        NoteItemWidget QLabel#tags_label, NoteItemWidget QLabel#date_label, SnippetItemWidget QLabel#lang_label, SnippetItemWidget QLabel#tags_label, SnippetItemWidget QLabel#date_label {{ color: #aaa; background-color: transparent; }}
        QListWidget::item:selected {{ background-color: {blue.name()}; border-radius: 2px; }}
        QListWidget::item:selected NoteItemWidget QLabel, QListWidget::item:selected SnippetItemWidget QLabel {{ color: {black.name()}; background-color: transparent; }}
        QListWidget::item:selected NoteItemWidget QLabel#tags_label, QListWidget::item:selected NoteItemWidget QLabel#date_label, QListWidget::item:selected SnippetItemWidget QLabel#lang_label, QListWidget::item:selected SnippetItemWidget QLabel#tags_label, QListWidget::item:selected SnippetItemWidget QLabel#date_label {{ color: #333; background-color: transparent; }}
        QListWidget::item:hover:!selected {{ background-color: {light_grey.name()}; border-radius: 2px; }}
        QComboBox {{ background-color: {dark_grey.name()}; border: 1px solid {grey.name()}; border-radius: 3px; padding: 3px 5px; min-width: 6em; color: {white.name()}; selection-background-color: {blue.name()}; selection-color: {black.name()}; }}
        QComboBox:hover {{ border: 1px solid {blue.name()}; }}
        QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 15px; border-left-width: 1px; border-left-color: {grey.name()}; border-left-style: solid; border-top-right-radius: 3px; border-bottom-right-radius: 3px; }}
        QComboBox QAbstractItemView {{ background-color: {black.name()}; border: 1px solid {grey.name()}; selection-background-color: {blue.name()}; selection-color: {black.name()}; color: {white.name()}; padding: 2px; }}
        QSpinBox {{ background-color: {black.name()}; color: {white.name()}; border: 1px solid {grey.name()}; border-radius: 3px; padding: 3px; selection-background-color: {blue.name()}; selection-color: {black.name()}; }}
        QSpinBox:hover {{ border: 1px solid {blue.name()}; }}
        QSpinBox::up-button, QSpinBox::down-button {{ width: 16px; border-left-width: 1px; border-left-color: {grey.name()}; border-left-style: solid; }}
        QToolBar {{ background-color: {dark_grey.name()}; border: 1px solid {grey.name()}; padding: 2px; spacing: 3px; }}
        QToolBar QToolButton {{ background-color: transparent; color: {white.name()}; border: 1px solid transparent; padding: 3px; margin: 1px; border-radius: 3px; }}
        QToolBar QToolButton:hover {{ background-color: {light_grey.name()}; border: 1px solid {grey.name()}; }}
        QToolBar QToolButton:pressed {{ background-color: {dark_blue.name()}; }}
        QToolBar QToolButton:checked {{ background-color: {blue.name()}; color: {black.name()}; border: 1px solid {dark_blue.name()}; }}
        QSplitter::handle {{ background-color: {grey.name()}; }}
        QSplitter::handle:horizontal {{ width: 2px; }}
        QSplitter::handle:vertical {{ height: 2px; }}
        QSplitter::handle:pressed {{ background-color: {blue.name()}; }}
        QStatusBar {{ background-color: {dark_grey.name()}; color: {white.name()}; border-top: 1px solid {grey.name()}; }}
        QStatusBar::item {{ border: none; }}
    """
    app.setStyleSheet(style_sheet)
    print("[style.py] Dark theme styles applied.")

def load_light_theme(app: QApplication):
    """Loads an explicit light theme palette and specific stylesheet."""
    print("[style.py] Loading explicit LIGHT theme...")
    app.setStyle("Fusion") # Or "Windows"

    palette = QPalette()
    # --- Define light theme colors including light_grey ---
    light_window = QColor(240, 240, 240)
    light_base = QColor(255, 255, 255)
    light_text = QColor(0, 0, 0)
    light_highlight = QColor(51, 153, 255)
    light_highlighted_text = QColor(255, 255, 255)
    light_button = QColor(225, 225, 225)
    light_button_text = QColor(0, 0, 0)
    light_link = QColor(0, 0, 238)
    light_link_visited = QColor(85, 26, 139)
    light_disabled_text = QColor(120, 120, 120)
    light_border = QColor(200, 200, 200)
    light_grey = QColor(211, 211, 211) # For hover states etc.
    # -----------------------------------------------------

    palette.setColor(QPalette.ColorRole.Window, light_window)
    palette.setColor(QPalette.ColorRole.WindowText, light_text)
    palette.setColor(QPalette.ColorRole.Base, light_base)
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 231, 227))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ColorRole.ToolTipText, light_text)
    palette.setColor(QPalette.ColorRole.Text, light_text)
    palette.setColor(QPalette.ColorRole.Button, light_button)
    palette.setColor(QPalette.ColorRole.ButtonText, light_button_text)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Highlight, light_highlight)
    palette.setColor(QPalette.ColorRole.HighlightedText, light_highlighted_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, light_disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, light_disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, light_disabled_text)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(210, 210, 210))
    palette.setColor(QPalette.ColorRole.Link, light_link)
    palette.setColor(QPalette.ColorRole.LinkVisited, light_link_visited)

    app.setPalette(palette)
    print("[style.py] Explicit light palette set.")

    # Apply stylesheet for light theme overrides
    light_style_sheet = f"""
        QWidget {{
            color: {light_text.name()}; /* Default text color */
            background-color: palette(window);
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser, QListWidget, QComboBox, QSpinBox {{
            background-color: palette(base);
            color: palette(text);
            border: 1px solid {light_border.name()};
        }}
        /* Ensure QGroupBox uses appropriate colors */
        QGroupBox {{
            border: 1px solid {light_border.name()};
            margin-top: 10px; padding-top: 5px; border-radius: 3px;
            color: {light_text.name()}; /* Explicit text color for groupbox itself */
        }}
         QGroupBox::title {{
             subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; left: 7px;
             color: {light_text.name()}; /* Explicit title color */
         }}
        QTextEdit a, QTextBrowser a {{
            color: palette(link);
            text-decoration: underline;
        }}
        QPushButton {{
            background-color: palette(button);
            color: palette(button-text);
            border: 1px solid {light_border.name()};
            padding: 5px 10px; border-radius: 3px; min-width: 70px;
        }}
         QPushButton:hover {{
             background-color: {light_highlight.lighter(160).name()}; /* Lighter hover */
             border: 1px solid {light_highlight.name()};
         }}
         QPushButton:pressed {{
             background-color: {light_highlight.darker(110).name()};
         }}
         QPushButton:disabled {{
             background-color: {light_window.name()};
             color: {light_disabled_text.name()};
             border-color: {light_grey.name()}; /* Use defined light_grey */
         }}
         /* Explicitly set text color for list items */
         QListWidget::item {{
             color: {light_text.name()};
         }}
         NoteItemWidget QLabel#title_label, SnippetItemWidget QLabel#title_label {{
              font-weight: bold;
              color: {light_text.name()};
          }}
         NoteItemWidget QLabel#tags_label, NoteItemWidget QLabel#date_label,
         SnippetItemWidget QLabel#lang_label, SnippetItemWidget QLabel#tags_label, SnippetItemWidget QLabel#date_label {{
              color: #555; /* Darker grey for details */
          }}
         QListWidget::item:selected {{
             background-color: palette(highlight);
             color: palette(highlighted-text);
         }}
         QListWidget::item:selected NoteItemWidget QLabel,
         QListWidget::item:selected SnippetItemWidget QLabel {{
              color: palette(highlighted-text);
          }}
         QListWidget::item:selected NoteItemWidget QLabel#tags_label,
         QListWidget::item:selected NoteItemWidget QLabel#date_label,
         QListWidget::item:selected SnippetItemWidget QLabel#lang_label,
         QListWidget::item:selected SnippetItemWidget QLabel#tags_label,
         QListWidget::item:selected SnippetItemWidget QLabel#date_label {{
              color: palette(highlighted-text); /* Keep details visible */
          }}
         QToolBar QToolButton:checked {{
            background-color: palette(highlight);
            color: palette(highlighted-text);
            border: 1px solid {light_highlight.darker(120).name()};
        }}
        QComboBox {{ color: palette(text); selection-background-color: palette(highlight); selection-color: palette(highlighted-text); }}
        QComboBox QAbstractItemView {{ color: palette(text); }} /* Ensure dropdown text color is correct */
    """
    app.setStyleSheet(light_style_sheet)
    print("[style.py] Explicit Light theme stylesheet applied.")

# utils/style.py
# --- END OF FILE utils/style.py ---