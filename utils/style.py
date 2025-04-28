# --- START OF FILE style.py ---

# utils/style.py
from PyQt6.QtGui import QColor, QPalette, QIcon # Added QIcon
from PyQt6.QtCore import Qt, QStandardPaths # Added QStandardPaths for icons path potentially
from PyQt6.QtWidgets import QStyle # Added QStyle

# --- Icon helper potentially moved here or kept in base_editor ---
# Assuming get_icon is available globally or imported if needed for custom tab close icon
# from ui.base_editor import get_icon # Example if moved from base_editor

def load_styles(app):
    """Loads a dark theme stylesheet and palette for the application."""
    app.setStyle("Fusion")

    palette = QPalette()
    dark_grey = QColor(53, 53, 53); grey = QColor(75, 75, 75); light_grey = QColor(90, 90, 90); black = QColor(35, 35, 35); white = QColor(240, 240, 240); blue = QColor(42, 130, 218); dark_blue = QColor(30, 100, 180); link_color = QColor(90, 170, 255);
    palette.setColor(QPalette.ColorRole.Window, dark_grey); palette.setColor(QPalette.ColorRole.WindowText, white); palette.setColor(QPalette.ColorRole.Base, black); palette.setColor(QPalette.ColorRole.AlternateBase, dark_grey); palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25)); palette.setColor(QPalette.ColorRole.ToolTipText, white); palette.setColor(QPalette.ColorRole.Text, white); palette.setColor(QPalette.ColorRole.Button, dark_grey); palette.setColor(QPalette.ColorRole.ButtonText, white); palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red); palette.setColor(QPalette.ColorRole.Highlight, blue); palette.setColor(QPalette.ColorRole.HighlightedText, black); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, grey); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, grey); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, grey); palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, grey);
    palette.setColor(QPalette.ColorRole.Link, link_color)
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(180, 140, 255))

    app.setPalette(palette)

    # --- Attempt to set a visible tab close button ---
    # Option 1: Use a standard pixmap if available
    close_icon_path = ""
    try:
        # Get standard icon using QStyle
        style = QApplication.style()
        if style:
            # SP_TitleBarCloseButton is a common one, might look okay
            close_icon = style.standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)
            # We need the path for the stylesheet's url(). This is tricky with standard icons.
            # A more reliable way is to save the pixmap to a temporary file or use a known custom icon.
            # Let's try using a known custom icon name first.
            close_icon_path = "icons/close_tab.png" # Assume you create this icon
            # Check if custom icon exists, otherwise fallback might not work well in CSS
            from pathlib import Path
            if not (Path(__file__).parent.parent / close_icon_path).exists():
                 print(f"Warning: Custom tab close icon '{close_icon_path}' not found. Falling back.")
                 close_icon_path = "" # Fallback to default or no icon styling
    except Exception as e:
        print(f"Error getting close icon: {e}")
        close_icon_path = ""

    # Define the CSS part for the close button
    tab_close_button_css = f"""
     QTabBar::close-button {{
         /* Use image if path is set, otherwise maybe just background/border */
         {"image: url(" + close_icon_path + ");" if close_icon_path else ""}
         background-color: transparent; /* Make background transparent */
         border: none; /* Remove border */
         border-radius: 2px;
         margin: 2px; /* Add some margin */
         padding: 2px; /* Add padding */
         subcontrol-position: right;
         subcontrol-origin: padding;
         /* Add a subtle border or background on hover for visibility */
     }}
     QTabBar::close-button:hover {{
         background-color: rgba(200, 200, 200, 80); /* Light greyish background */
         border: 1px solid {grey.name()};
     }}
     QTabBar::close-button:pressed {{
         background-color: rgba(150, 150, 150, 120);
     }}
     """
    # --------------------------------------------------

    style_sheet = f"""
    QToolTip {{ color: {white.name()}; background-color: {blue.name()}; border: 1px solid {white.name()}; padding: 4px; opacity: 220; }}
    QMainWindow {{ background-color: {dark_grey.name()}; }}
    QWidget {{ color: {white.name()}; }}

    QTabWidget::pane {{ border: 1px solid {grey.name()}; top: -1px; background-color: {dark_grey.name()}; }}
    QTabWidget::tab-bar {{ left: 5px; }}
    QTabBar::tab {{
        background: {dark_grey.name()}; color: {white.name()}; border: 1px solid {grey.name()};
        border-bottom-color: {grey.name()}; border-top-left-radius: 4px; border-top-right-radius: 4px;
        min-width: 8ex; padding: 5px 10px; margin-right: 2px;
        /* Make space for close button */
        padding-right: 25px;
    }}
    QTabBar::tab:selected {{ background: {blue.name()}; color: {black.name()}; border-color: {blue.name()}; border-bottom-color: {blue.name()}; }}
    QTabBar::tab:!selected:hover {{ background: {light_grey.name()}; }}

    /* --- Include the Tab Close Button CSS --- */
    {tab_close_button_css}
    /* -------------------------------------- */

    QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser {{
        background-color: {black.name()}; color: {white.name()}; border: 1px solid {grey.name()};
        border-radius: 3px; padding: 4px;
        selection-background-color: {blue.name()}; selection-color: {black.name()};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus {{ border: 1px solid {blue.name()}; }}

    QTextEdit a {{ color: palette(link); text-decoration: underline; }}

    QPushButton {{ background-color: {dark_grey.name()}; color: {white.name()}; border: 1px solid {grey.name()}; padding: 5px 10px; border-radius: 3px; min-width: 70px; }}
    QPushButton:hover {{ background-color: {light_grey.name()}; border: 1px solid {blue.name()}; }}
    QPushButton:pressed {{ background-color: {dark_blue.name()}; }}
    QPushButton:disabled {{ background-color: {grey.name()}; color: {light_grey.name()}; border-color: {dark_grey.name()}; }}

    QListWidget {{ background-color: {black.name()}; border: 1px solid {grey.name()}; border-radius: 3px; padding: 2px; outline: 0; }}
    NoteItemWidget QLabel#title_label, SnippetItemWidget QLabel#title_label {{ font-weight: bold; color: {white.name()}; }}
    NoteItemWidget QLabel#tags_label, NoteItemWidget QLabel#date_label,
    SnippetItemWidget QLabel#lang_label, SnippetItemWidget QLabel#tags_label, SnippetItemWidget QLabel#date_label {{ color: #aaa; }}
    QListWidget::item:selected NoteItemWidget QLabel, QListWidget::item:selected SnippetItemWidget QLabel {{ color: {black.name()}; }}
    QListWidget::item:selected NoteItemWidget QLabel#tags_label, QListWidget::item:selected NoteItemWidget QLabel#date_label, QListWidget::item:selected SnippetItemWidget QLabel#lang_label, QListWidget::item:selected SnippetItemWidget QLabel#tags_label, QListWidget::item:selected SnippetItemWidget QLabel#date_label {{ color: #333; }}
    QListWidget::item:selected {{ background-color: {blue.name()}; border-radius: 2px; }}
    QListWidget::item:hover:!selected {{ background-color: {light_grey.name()}; border-radius: 2px; }}

    QComboBox {{ background-color: {dark_grey.name()}; border: 1px solid {grey.name()}; border-radius: 3px; padding: 3px 5px; min-width: 6em; }}
    QComboBox:hover {{ border: 1px solid {blue.name()}; }}
    QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 15px; border-left-width: 1px; border-left-color: {grey.name()}; border-left-style: solid; border-top-right-radius: 3px; border-bottom-right-radius: 3px; }}
    QComboBox::down-arrow {{}}
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
    print("Dark theme styles loaded.")

# utils/style.py
# --- END OF FILE style.py ---