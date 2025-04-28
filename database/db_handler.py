# database/db_handler.py

import sqlite3
from pathlib import Path
from typing import Optional

class DBHandler:
    """
    Manages the SQLite database connection and initialization.
    Ensures the connection is usable by multiple threads if configured.
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self):
        """Establishes the database connection and initializes tables."""
        try:
            # Connect allowing access from multiple threads (worker threads).
            # DataManager methods using this connection should handle concurrency
            # (e.g., using separate cursors per operation).
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            # Enable row factory for accessing columns by name
            self.connection.row_factory = sqlite3.Row
            self._init_db()
            print(f"DBHandler: Database connected successfully: {self.db_path}")
        except sqlite3.Error as e:
            print(f"DBHandler: Database connection error to {self.db_path}: {e}")
            self.connection = None # Ensure connection is None if failed

    def _init_db(self):
        """Initializes database tables if they don't exist."""
        if not self.connection:
             print("DBHandler: Cannot initialize DB - no connection.")
             return
        try:
            cursor = self.connection.cursor()
            print("DBHandler: Checking/Creating database tables...")

            # Notes table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)

            # Snippets table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                code TEXT,
                language TEXT,
                tags TEXT,
                created_at TEXT NOT NULL
            )
            """)
            # Add potential indexes for searching common fields
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_tags ON notes(tags)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snippets_tags ON snippets(tags)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_snippets_language ON snippets(language)")


            self.connection.commit()
            cursor.close()
            print("DBHandler: Database tables checked/initialized.")
        except sqlite3.Error as e:
             print(f"DBHandler: Error initializing database tables: {e}")
             # Attempt rollback if initialization fails partially
             try:
                 self.connection.rollback()
             except sqlite3.Error as rb_err:
                 print(f"DBHandler: Rollback failed after init error: {rb_err}")


    def close(self):
        """Closes the database connection."""
        if self.connection:
             print(f"DBHandler: Closing database connection to {self.db_path}...")
             self.connection.close()
             self.connection = None
             print("DBHandler: Database connection closed.")

    # Destructor to ensure connection is closed if handler object is deleted
    def __del__(self):
        self.close()

# database/db_handler.py
# --- END OF FILE db_handler.py ---
