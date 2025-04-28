# --- START OF FILE database/data_manager.py ---

# database/data_manager.py

import sqlite3
from pathlib import Path
from typing import List, Optional, Callable, Any, Set, Tuple
from datetime import datetime
from .db_handler import DBHandler
from .models import Note, Snippet, RecentItem
from .db_worker import DBWorker
from PyQt6.QtCore import QThreadPool, QObject, pyqtSignal

# Define database path in user's home directory
HOME_DIR = Path.home()
APP_DATA_DIR = HOME_DIR / ".notes_manager"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = APP_DATA_DIR / "notes.db"
print(f"Database Path: {DB_PATH}")

class DataManager(QObject):
    """Manages data operations with background threading."""
    note_added = pyqtSignal(Note)
    note_updated = pyqtSignal(Note)
    note_deleted = pyqtSignal(int)
    all_notes_loaded = pyqtSignal(list)
    note_searched = pyqtSignal(list)
    snippet_added = pyqtSignal(Snippet)
    snippet_updated = pyqtSignal(Snippet)
    snippet_deleted = pyqtSignal(int)
    all_snippets_loaded = pyqtSignal(list)
    snippet_searched = pyqtSignal(list)
    recent_items_loaded = pyqtSignal(list)
    all_tags_loaded = pyqtSignal(list)
    tags_updated = pyqtSignal()
    db_error = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        print("DataManager: Initializing...")
        self._db_handler = DBHandler(DB_PATH)
        self._thread_pool = QThreadPool(self)
        print(f"DataManager: Thread pool configured with max {self._thread_pool.maxThreadCount()} threads.")
        self._active_tasks = {}

    def _submit_task(self, task_id_prefix: str, method: Callable, args: tuple = (), result_signal: Optional[pyqtSignal] = None, error_signal: pyqtSignal = db_error, finished_callback: Optional[Callable] = None):
        timestamp = datetime.now().timestamp()
        task_id = f"{task_id_prefix}_{id(args)}_{timestamp}"
        while task_id in self._active_tasks:
            timestamp += 0.000001
            task_id = f"{task_id_prefix}_{id(args)}_{timestamp}"
        print(f"DataManager: Submitting async task '{task_id}' for method '{method.__name__}'")
        worker = DBWorker(task_id, method, args=args)
        if result_signal:
            worker.signals.result.connect(lambda tid, res: result_signal.emit(res) if tid == task_id else None)
        worker.signals.error.connect(lambda tid, err: self.db_error.emit(tid, err) if tid == task_id else None)
        worker.signals.finished.connect(lambda tid: (
             self._active_tasks.pop(tid, None),
             finished_callback(tid) if finished_callback else None
             ) if tid == task_id else None)
        self._active_tasks[task_id] = worker
        self._thread_pool.start(worker)

    # ==============================================================
    # Async Methods (Modified for List[str] tag filtering)
    # ==============================================================

    def load_all_notes_async(self, filter_tags: Optional[List[str]] = None):
        args = (filter_tags,)
        self._submit_task("load_all_notes", self._execute_get_all_notes, args=args, result_signal=self.all_notes_loaded)

    def search_notes_async(self, query: str, filter_tags: Optional[List[str]] = None):
        args = (query, filter_tags)
        self._submit_task("search_notes", self._execute_search_notes, args=args, result_signal=self.note_searched)

    def add_note_async(self, note: Note):
        callback = lambda tid: self.tags_updated.emit()
        self._submit_task("add_note", self._execute_add_note, args=(note,), result_signal=self.note_added, finished_callback=callback)

    def update_note_async(self, note: Note):
        callback = lambda tid: self.tags_updated.emit()
        self._submit_task("update_note", self._execute_update_note, args=(note,), result_signal=self.note_updated, finished_callback=callback)

    def delete_note_async(self, note_id: int):
        task_id = f"delete_note_{note_id}_{datetime.now().timestamp()}"
        worker = DBWorker(task_id, self._execute_delete_note, args=(note_id,))
        worker.signals.result.connect(lambda tid, success: self.note_deleted.emit(note_id) if tid == task_id and success else None)
        worker.signals.error.connect(lambda tid, err: self.db_error.emit(tid, err) if tid == task_id else None)
        worker.signals.finished.connect(lambda tid: (
            self._active_tasks.pop(tid, None),
            self.tags_updated.emit()
            ) if tid == task_id else None)
        self._active_tasks[task_id] = worker
        self._thread_pool.start(worker)

    def load_all_snippets_async(self, filter_tags: Optional[List[str]] = None):
        args = (filter_tags,)
        self._submit_task("load_all_snippets", self._execute_get_all_snippets, args=args, result_signal=self.all_snippets_loaded)

    def search_snippets_async(self, query: str, filter_tags: Optional[List[str]] = None):
        args = (query, filter_tags)
        self._submit_task("search_snippets", self._execute_search_snippets, args=args, result_signal=self.snippet_searched)

    def add_snippet_async(self, snippet: Snippet):
        callback = lambda tid: self.tags_updated.emit()
        self._submit_task("add_snippet", self._execute_add_snippet, args=(snippet,), result_signal=self.snippet_added, finished_callback=callback)

    def update_snippet_async(self, snippet: Snippet):
        callback = lambda tid: self.tags_updated.emit()
        self._submit_task("update_snippet", self._execute_update_snippet, args=(snippet,), result_signal=self.snippet_updated, finished_callback=callback)

    def delete_snippet_async(self, snippet_id: int):
        task_id = f"delete_snippet_{snippet_id}_{datetime.now().timestamp()}"
        worker = DBWorker(task_id, self._execute_delete_snippet, args=(snippet_id,))
        worker.signals.result.connect(lambda tid, success: self.snippet_deleted.emit(snippet_id) if tid == task_id and success else None)
        worker.signals.error.connect(lambda tid, err: self.db_error.emit(tid, err) if tid == task_id else None)
        worker.signals.finished.connect(lambda tid: (
             self._active_tasks.pop(tid, None),
             self.tags_updated.emit()
             ) if tid == task_id else None)
        self._active_tasks[task_id] = worker
        self._thread_pool.start(worker)

    def load_all_tags_async(self):
        self._submit_task("load_all_tags", self._execute_get_all_tags, result_signal=self.all_tags_loaded)

    # --- Sync Methods (Corrected try/except/finally) ---
    def get_note_sync(self, note_id: int) -> Optional[Note]:
        print(f"DataManager: Executing synchronous get_note_sync for ID {note_id}")
        cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            cursor.execute("SELECT * FROM notes WHERE id=?", (note_id,))
            row = cursor.fetchone()
            # --- Corrected: Return after try or in except/finally ---
            if row:
                return Note.from_db_row(row)
            else:
                return None
        except Exception as e:
            print(f"DataManager Sync Error (get_note_sync ID {note_id}): {e}")
            return None
        finally:
            if cursor:
                cursor.close()
        # --- Removed return None here ---

    def get_snippet_sync(self, snippet_id: int) -> Optional[Snippet]:
        print(f"DataManager: Executing synchronous get_snippet_sync for ID {snippet_id}")
        cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            cursor.execute("SELECT * FROM snippets WHERE id=?", (snippet_id,))
            row = cursor.fetchone()
            # --- Corrected: Return after try or in except/finally ---
            if row:
                return Snippet.from_db_row(row)
            else:
                return None
        except Exception as e:
            print(f"DataManager Sync Error (get_snippet_sync ID {snippet_id}): {e}")
            return None
        finally:
            if cursor:
                cursor.close()
        # --- Removed return None here ---
    # -----------------------------------------------------

    # ==============================================================
    # Internal Execution Methods (Updated for OR tag filtering)
    # ==============================================================

    def _build_tag_filter_sql(self, filter_tags: Optional[List[str]]) -> Tuple[str, List[str]]:
        if not filter_tags:
            return "", []
        clauses = ["(',' || tags || ',') LIKE ?"] * len(filter_tags)
        sql_clause = f" ({' OR '.join(clauses)})" # Condition part only
        params = [f"%,{tag},%" for tag in filter_tags]
        return sql_clause, params

    def _execute_get_all_notes(self, filter_tags: Optional[List[str]] = None) -> List[Note]:
        print(f"DataManager Worker: Executing _execute_get_all_notes (Filter Tags: {filter_tags or 'None'})")
        notes = []
        cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            query = "SELECT * FROM notes"
            tag_sql, tag_params = self._build_tag_filter_sql(filter_tags)
            params = []
            if tag_sql:
                 query += " WHERE" + tag_sql # Add WHERE if tags exist
                 params.extend(tag_params)
            query += " ORDER BY updated_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            notes = [Note.from_db_row(row) for row in rows]
            print(f"DataManager Worker: _execute_get_all_notes found {len(notes)} notes.")
        except Exception as e:
            print(f"DataManager Worker Error (_execute_get_all_notes): {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
        return notes

    def _execute_search_notes(self, query: str, filter_tags: Optional[List[str]] = None) -> List[Note]:
        print(f"DataManager Worker: Executing _execute_search_notes (Query: '{query}', Filter Tags: {filter_tags or 'None'})")
        notes = []
        cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            search_term = f"%{query}%"
            base_query = "SELECT * FROM notes WHERE (title LIKE ? OR content LIKE ? OR tags LIKE ?)"
            params = [search_term, search_term, search_term]
            tag_sql, tag_params = self._build_tag_filter_sql(filter_tags)
            if tag_sql:
                base_query += " AND" + tag_sql # Append the AND (...) part
                params.extend(tag_params)
            base_query += " ORDER BY updated_at DESC"
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            notes = [Note.from_db_row(row) for row in rows]
            print(f"DataManager Worker: _execute_search_notes found {len(notes)} notes.")
        except Exception as e:
            print(f"DataManager Worker Error (_execute_search_notes): {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
        return notes

    def _execute_get_all_snippets(self, filter_tags: Optional[List[str]] = None) -> List[Snippet]:
        print(f"DataManager Worker: Executing _execute_get_all_snippets (Filter Tags: {filter_tags or 'None'})")
        snippets = []
        cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            query = "SELECT * FROM snippets"
            tag_sql, tag_params = self._build_tag_filter_sql(filter_tags)
            params = []
            if tag_sql:
                 query += " WHERE" + tag_sql
                 params.extend(tag_params)
            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            snippets = [Snippet.from_db_row(row) for row in rows]
            print(f"DataManager Worker: _execute_get_all_snippets found {len(snippets)} snippets.")
        except Exception as e:
            print(f"DataManager Worker Error (_execute_get_all_snippets): {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
        return snippets

    def _execute_search_snippets(self, query: str, filter_tags: Optional[List[str]] = None) -> List[Snippet]:
        print(f"DataManager Worker: Executing _execute_search_snippets (Query: '{query}', Filter Tags: {filter_tags or 'None'})")
        snippets = []
        cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            search_term = f"%{query}%"
            base_query = "SELECT * FROM snippets WHERE (title LIKE ? OR code LIKE ? OR tags LIKE ? OR language LIKE ?)"
            params = [search_term, search_term, search_term, search_term]
            tag_sql, tag_params = self._build_tag_filter_sql(filter_tags)
            if tag_sql:
                base_query += " AND" + tag_sql
                params.extend(tag_params)
            base_query += " ORDER BY created_at DESC"
            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            snippets = [Snippet.from_db_row(row) for row in rows]
            print(f"DataManager Worker: _execute_search_snippets found {len(snippets)} snippets.")
        except Exception as e:
            print(f"DataManager Worker Error (_execute_search_snippets): {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
        return snippets

    def _execute_get_all_tags(self) -> List[str]:
        print("DataManager Worker: Executing _execute_get_all_tags")
        all_tags: Set[str] = set()
        cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            cursor.execute("SELECT tags FROM notes WHERE tags IS NOT NULL AND tags != ''")
            note_tag_rows = cursor.fetchall()
            cursor.execute("SELECT tags FROM snippets WHERE tags IS NOT NULL AND tags != ''")
            snippet_tag_rows = cursor.fetchall()

            for row in note_tag_rows:
                tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()]
                all_tags.update(tags)
            for row in snippet_tag_rows:
                tags = [tag.strip() for tag in row['tags'].split(',') if tag.strip()]
                all_tags.update(tags)

            sorted_tags = sorted(list(all_tags))
            print(f"DataManager Worker: _execute_get_all_tags found {len(sorted_tags)} unique tags.")
            return sorted_tags
        except Exception as e:
            print(f"DataManager Worker Error (_execute_get_all_tags): {e}")
            raise e
        finally:
             if cursor:
                 cursor.close()

    def _execute_add_note(self, note: Note) -> Optional[Note]:
        print(f"DataManager Worker: Executing _execute_add_note for Note Title '{note.title}'")
        now = datetime.now().isoformat(); new_note = None
        conn = self._db_handler.connection; cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO notes (title, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",(note.title, note.content or "", note.tags or "", now, now))
            new_id = cursor.lastrowid; conn.commit(); cursor.close(); cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE id = ?", (new_id,))
            row = cursor.fetchone(); new_note = Note.from_db_row(row) if row else None
            if new_note: print(f"DataManager Worker: _execute_add_note successful. New ID: {new_note.id}")
        except Exception as e: print(f"DataManager Worker Error (_execute_add_note): {e}"); conn.rollback(); raise e
        finally:
            if cursor: cursor.close()
        return new_note

    def _execute_update_note(self, note: Note) -> Optional[Note]:
        print(f"DataManager Worker: Executing _execute_update_note for Note ID {note.id}")
        if note.id is None: raise ValueError("Cannot update note with None ID")
        now = datetime.now().isoformat(); updated_note = None
        conn = self._db_handler.connection; cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE notes SET title=?, content=?, tags=?, updated_at=? WHERE id=?", (note.title, note.content or "", note.tags or "", now, note.id))
            conn.commit(); cursor.close(); cursor = conn.cursor()
            cursor.execute("SELECT * FROM notes WHERE id = ?", (note.id,))
            row = cursor.fetchone(); updated_note = Note.from_db_row(row) if row else None
            if updated_note: print(f"DataManager Worker: _execute_update_note successful for ID {note.id}")
        except Exception as e: print(f"DataManager Worker Error (_execute_update_note ID {note.id}): {e}"); conn.rollback(); raise e
        finally:
            if cursor: cursor.close()
        return updated_note

    def _execute_delete_note(self, note_id: int) -> bool:
        print(f"DataManager Worker: Executing _execute_delete_note for Note ID {note_id}")
        success = False; conn = self._db_handler.connection; cursor = None
        try:
            cursor = conn.cursor(); cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
            conn.commit(); success = cursor.rowcount > 0
            print(f"DataManager Worker: _execute_delete_note successful for ID {note_id}: {success}")
        except Exception as e: print(f"DataManager Worker Error (_execute_delete_note ID {note_id}): {e}"); conn.rollback(); raise e
        finally:
            if cursor: cursor.close()
        return success

    def _execute_add_snippet(self, snippet: Snippet) -> Optional[Snippet]:
        print(f"DataManager Worker: Executing _execute_add_snippet for Snippet Title '{snippet.title}'")
        now = datetime.now().isoformat(); new_snippet = None
        conn = self._db_handler.connection; cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO snippets (title, code, language, tags, created_at) VALUES (?, ?, ?, ?, ?)", (snippet.title, snippet.code or "", snippet.language or "Text", snippet.tags or "", now))
            new_id = cursor.lastrowid; conn.commit(); cursor.close(); cursor = conn.cursor()
            cursor.execute("SELECT * FROM snippets WHERE id = ?", (new_id,))
            row = cursor.fetchone(); new_snippet = Snippet.from_db_row(row) if row else None
            if new_snippet: print(f"DataManager Worker: _execute_add_snippet successful. New ID: {new_snippet.id}")
        except Exception as e: print(f"DataManager Worker Error (_execute_add_snippet): {e}"); conn.rollback(); raise e
        finally:
             if cursor: cursor.close()
        return new_snippet

    def _execute_update_snippet(self, snippet: Snippet) -> Optional[Snippet]:
        print(f"DataManager Worker: Executing _execute_update_snippet for Snippet ID {snippet.id}")
        if snippet.id is None: raise ValueError("Cannot update snippet with None ID")
        updated_snippet = None; conn = self._db_handler.connection; cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE snippets SET title=?, code=?, language=?, tags=? WHERE id=?", (snippet.title, snippet.code or "", snippet.language or "Text", snippet.tags or "", snippet.id))
            conn.commit(); cursor.close(); cursor = conn.cursor()
            cursor.execute("SELECT * FROM snippets WHERE id = ?", (snippet.id,))
            row = cursor.fetchone(); updated_snippet = Snippet.from_db_row(row) if row else None
            if updated_snippet: print(f"DataManager Worker: _execute_update_snippet successful for ID {snippet.id}")
        except Exception as e: print(f"DataManager Worker Error (_execute_update_snippet ID {snippet.id}): {e}"); conn.rollback(); raise e
        finally:
             if cursor: cursor.close()
        return updated_snippet

    def _execute_delete_snippet(self, snippet_id: int) -> bool:
        print(f"DataManager Worker: Executing _execute_delete_snippet for Snippet ID {snippet_id}")
        success = False; conn = self._db_handler.connection; cursor = None
        try:
            cursor = conn.cursor(); cursor.execute("DELETE FROM snippets WHERE id=?", (snippet_id,)); conn.commit(); success = cursor.rowcount > 0
            print(f"DataManager Worker: _execute_delete_snippet successful for ID {snippet_id}: {success}")
        except Exception as e: print(f"DataManager Worker Error (_execute_delete_snippet ID {snippet_id}): {e}"); conn.rollback(); raise e
        finally:
             if cursor: cursor.close()
        return success

    def _execute_get_recent_items(self, limit: int) -> List[RecentItem]:
        print(f"DataManager Worker: Executing _execute_get_recent_items limit {limit}")
        recent_items = []; cursor = None
        try:
            cursor = self._db_handler.connection.cursor()
            query = """ SELECT type, id, title, created_at, updated_at, last_activity_at FROM (SELECT 'note' as type, id, title, created_at, updated_at, updated_at as last_activity_at FROM notes UNION ALL SELECT 'snippet' as type, id, title, created_at, NULL as updated_at, created_at as last_activity_at FROM snippets ) ORDER BY last_activity_at DESC LIMIT ? """
            cursor.execute(query, (limit,)); rows = cursor.fetchall()
            recent_items = [RecentItem.from_db_row(row) for row in rows]
            print(f"DataManager Worker: _execute_get_recent_items found {len(recent_items)} items.")
        except Exception as e: print(f"DataManager Worker Error (_execute_get_recent_items): {e}"); raise e
        finally:
             if cursor: cursor.close()
        return recent_items

    # ==============================================================
    # Shutdown
    # ==============================================================
    def shutdown(self):
        print("DataManager: Shutting down...")
        active_threads = self._thread_pool.activeThreadCount()
        if active_threads > 0:
            print(f"DataManager: Waiting for {active_threads} active threads in pool...")
            self._thread_pool.waitForDone()
            print("DataManager: Thread pool finished.")
        else:
            print("DataManager: Thread pool already idle.")
        self.close_db()
        print("DataManager: Shutdown complete.")

    def close_db(self):
        print("DataManager: Closing DB connection.")
        if self._db_handler:
            self._db_handler.close()


# database/data_manager.py
# --- END OF FILE database/data_manager.py ---