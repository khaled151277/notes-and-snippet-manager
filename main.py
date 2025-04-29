# --- START OF FILE main.py ---

# main.py
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from database.data_manager import DataManager, DB_PATH

SETTINGS_FILE = DB_PATH.parent / "settings.json"
print(f"[main.py] Settings File Path: {SETTINGS_FILE}")

DEFAULT_SETTINGS = {
    "save_window_geometry": True,
    "window_geometry": {"x": None, "y": None, "width": 1200, "height": 700},
    "window_maximized": False,
    "main_splitter_sizes": None,
    "sidebar_splitter_sizes": None,
    "theme": "dark",
    "default_note_font_family": None,
    "default_note_font_size": 10
}

def load_settings() -> dict:
    print("[main.py] Loading settings...") # DEBUG
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                print(f"[main.py] Settings loaded from file: {settings}") # DEBUG
                loaded_settings = DEFAULT_SETTINGS.copy()
                loaded_settings.update(settings)
                if not isinstance(loaded_settings.get("window_geometry"), dict):
                    loaded_settings["window_geometry"] = DEFAULT_SETTINGS["window_geometry"].copy()
                print(f"[main.py] Final settings after merge: {loaded_settings}") # DEBUG
                return loaded_settings
        except (json.JSONDecodeError, IOError, TypeError) as e:
            print(f"[main.py] Error loading settings file ({SETTINGS_FILE}): {e}. Using defaults.")
            return DEFAULT_SETTINGS.copy()
    else:
        print(f"[main.py] Settings file not found. Creating default settings at: {SETTINGS_FILE}")
        try:
             SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
             with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                 json.dump(DEFAULT_SETTINGS, f, indent=2)
             return DEFAULT_SETTINGS.copy()
        except IOError as e:
            print(f"[main.py] Error creating default settings file ({SETTINGS_FILE}): {e}")
            return DEFAULT_SETTINGS.copy()

def save_settings(settings: dict):
    print("[main.py] Saving settings...") # DEBUG
    geom = settings.get("window_geometry", {})
    for key in ["x", "y", "width", "height"]:
        if geom.get(key) is not None:
            try: geom[key] = int(geom[key])
            except (ValueError, TypeError): geom[key] = None
    try:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print(f"[main.py] Settings saved to {SETTINGS_FILE}") # DEBUG
    except IOError as e: print(f"[main.py] Error saving settings file ({SETTINGS_FILE}): {e}")
    except TypeError as e: print(f"[main.py] Error serializing settings to JSON: {e}")

def main():
    app = QApplication(sys.argv)

    settings = load_settings()

    # --- Read theme and DEBUG ---
    current_theme = settings.get("theme", "dark").lower()
    print(f"[main.py] Theme read from settings: '{current_theme}'")
    # -----------------------------
    try:
        from utils.style import load_styles
        print(f"[main.py] Calling load_styles with theme_name='{current_theme}'") # DEBUG
        load_styles(app, theme_name=current_theme)
    except ImportError:
        print("[main.py] Note: Styles module not found. Using default styling.")
    except TypeError:
         print("[main.py] Note: Styles module found, but doesn't support theme selection yet. Applying default styles.")
         try:
            from utils.style import load_styles
            print("[main.py] Calling load_styles without theme_name (fallback)") # DEBUG
            load_styles(app)
         except Exception as e:
             print(f"[main.py] Failed to load styles: {e}")

    data_manager = DataManager()
    window = MainWindow(data_manager, settings)
    print("[main.py] Restoring geometry and showing window...") # DEBUG
    window._restore_geometry_and_state()
    window.show()
    print("[main.py] Entering event loop...") # DEBUG

    exit_code = app.exec()

    # --- Save settings on exit ---
    current_save_pref = window.settings.get("save_window_geometry", True)
    print(f"[main.py] Exiting. Save window geometry preference: {current_save_pref}")
    if current_save_pref:
        is_maximized = window.isMaximized()
        settings["window_maximized"] = is_maximized
        if not is_maximized:
            geo = window.geometry()
            settings["window_geometry"]["x"] = geo.x()
            settings["window_geometry"]["y"] = geo.y()
            settings["window_geometry"]["width"] = geo.width()
            settings["window_geometry"]["height"] = geo.height()
            print(f"[main.py] Saving window geometry: {settings['window_geometry']}")
        else: print("[main.py] Window is maximized, not saving specific geometry.")
        if hasattr(window, 'main_splitter'): settings["main_splitter_sizes"] = window.main_splitter.sizes(); print(f"[main.py] Saving main splitter sizes: {settings['main_splitter_sizes']}")
        if hasattr(window, 'list_tag_splitter'): settings["sidebar_splitter_sizes"] = window.list_tag_splitter.sizes(); print(f"[main.py] Saving sidebar splitter sizes: {settings['sidebar_splitter_sizes']}")
    else:
        settings["window_geometry"]["x"] = None; settings["window_geometry"]["y"] = None
        settings["window_maximized"] = False; settings["main_splitter_sizes"] = None; settings["sidebar_splitter_sizes"] = None
        print("[main.py] Saving disabled, clearing geometry settings.")
    save_settings(settings)
    # -----------------------------

    print("Application event loop finished. Shutting down DataManager.")
    data_manager.shutdown()
    print("DataManager shutdown complete. Exiting.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
# main.py
# --- END OF FILE main.py ---