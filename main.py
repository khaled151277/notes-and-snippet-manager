# main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from database.data_manager import DataManager

def main():
    app = QApplication(sys.argv)

    # Attempt to load styles (if they exist)
    try:
        from utils.style import load_styles
        load_styles(app)
    except ImportError:
        print("Note: Styles module not found. Using default styling.")

    # Create DataManager and pass it to the MainWindow
    data_manager = DataManager()
    window = MainWindow(data_manager)
    window.show()

    # Ensure database connection is closed when the app exits
    exit_code = app.exec()
    # Make sure DataManager is shut down, which closes the Thread Pool and DB connection
    print("Application event loop finished. Shutting down DataManager.")
    data_manager.shutdown() # Call shutdown to wait for workers and close DB
    print("DataManager shutdown complete. Exiting.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
# main.py
# --- END OF FILE main.py ---
