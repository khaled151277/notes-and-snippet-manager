# --- START OF FILE ui/main_window.py ---

# ui/main_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QListWidget, QLineEdit, QPushButton, QSplitter, QMessageBox, QLabel,
    QStyle, QListWidgetItem,
    QGroupBox, QSpacerItem, QSizePolicy,
    QCheckBox, QFormLayout, QTabBar, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer, QByteArray, QUrl
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QDesktopServices
from typing import Optional, Any, List, Dict
from database.data_manager import DataManager
from widgets.note_item import NoteItem
from widgets.snippet_item import SnippetItem
from ui.note_editor import NoteEditor
from ui.snippet_editor import SnippetEditor
from database.models import Note, Snippet
from ui.base_editor import get_icon

class MainWindow(QMainWindow):
    def __init__(self, data_manager: DataManager, settings: Dict):
        super().__init__()
        self.data_manager = data_manager
        self.settings = settings
        self.setWindowTitle("Notes & Snippets Manager")
        self._is_closing = False
        self._current_tag_filter: Optional[str] = None # Back to Optional[str]
        self._connect_data_manager_signals()
        self._setup_ui()
        self._setup_shortcuts()
        self._restore_geometry_and_state()
        self._reload_all_data(refresh_tags=True)

    def _connect_data_manager_signals(self):
        self.data_manager.note_added.connect(lambda note: self._handle_note_added(note) if not self._is_closing else None)
        self.data_manager.note_updated.connect(lambda note: self._handle_note_updated(note) if not self._is_closing else None)
        self.data_manager.note_deleted.connect(lambda note_id: self._handle_note_deleted(note_id) if not self._is_closing else None)
        self.data_manager.all_notes_loaded.connect(lambda notes: self._handle_all_notes_loaded(notes) if not self._is_closing else None)
        self.data_manager.note_searched.connect(lambda notes: self._handle_note_searched(notes) if not self._is_closing else None)
        self.data_manager.snippet_added.connect(lambda snippet: self._handle_snippet_added(snippet) if not self._is_closing else None)
        self.data_manager.snippet_updated.connect(lambda snippet: self._handle_snippet_updated(snippet) if not self._is_closing else None)
        self.data_manager.snippet_deleted.connect(lambda snippet_id: self._handle_snippet_deleted(snippet_id) if not self._is_closing else None)
        self.data_manager.all_snippets_loaded.connect(lambda snippets: self._handle_all_snippets_loaded(snippets) if not self._is_closing else None)
        self.data_manager.snippet_searched.connect(lambda snippets: self._handle_snippet_searched(snippets) if not self._is_closing else None)
        self.data_manager.all_tags_loaded.connect(self._handle_all_tags_loaded)
        self.data_manager.tags_updated.connect(self._refresh_tag_list)
        self.data_manager.db_error.connect(self._handle_db_error)

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 6, 0, 6)
        sidebar_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search items...")
        self.search_input.textChanged.connect(self._trigger_search)
        sidebar_layout.addWidget(self.search_input)

        self.list_tag_splitter = QSplitter(Qt.Orientation.Vertical)

        self.item_tabs = QTabWidget() # Holds lists AND settings now
        self.notes_list = QListWidget()
        self.snippets_list = QListWidget()
        self.item_tabs.addTab(self.notes_list, "Notes")
        self.item_tabs.addTab(self.snippets_list, "Snippets")
        self.notes_list.itemClicked.connect(self._on_note_selected)
        self.notes_list.itemDoubleClicked.connect(self._on_note_selected)
        self.snippets_list.itemClicked.connect(self._on_snippet_selected)
        self.snippets_list.itemDoubleClicked.connect(self._on_snippet_selected)

        self.settings_widget = QWidget()
        settings_tab_layout = QVBoxLayout(self.settings_widget)
        settings_tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        settings_form_layout = QFormLayout()
        settings_form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.save_geom_checkbox = QCheckBox("Save window size and position on exit")
        self.save_geom_checkbox.setChecked(self.settings.get("save_window_geometry", True))
        self.save_geom_checkbox.stateChanged.connect(self._on_save_geometry_changed)
        settings_form_layout.addRow(self.save_geom_checkbox)
        self.theme_combo = QComboBox()
        available_themes = {"Dark": "dark", "Light (Default)": "light"}
        current_theme_setting = self.settings.get("theme", "dark")
        current_index = 0
        i = 0
        for display_name, setting_name in available_themes.items():
            self.theme_combo.addItem(display_name, setting_name)
            if setting_name == current_theme_setting:
                current_index = i
            i += 1
        self.theme_combo.setCurrentIndex(current_index)
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        settings_form_layout.addRow("Theme (Requires Restart):", self.theme_combo)
        donate_button = QPushButton(get_icon("donate.png", QStyle.StandardPixmap.SP_DialogApplyButton), "Donate")
        donate_button.setToolTip("If you found the program useful, please support us with a donation")
        donate_button.clicked.connect(self._open_donate_link)
        donate_layout = QHBoxLayout()
        donate_layout.addStretch(1)
        donate_layout.addWidget(donate_button)
        donate_layout.addStretch(1)
        settings_tab_layout.addLayout(settings_form_layout)
        settings_tab_layout.addStretch(1)
        settings_tab_layout.addLayout(donate_layout)
        self.item_tabs.addTab(self.settings_widget, "Settings") # Add Settings to sidebar tabs

        self.list_tag_splitter.addWidget(self.item_tabs)

        self.tag_group_box = QGroupBox("Filter by Tag") # Simplified title
        tag_layout = QVBoxLayout(self.tag_group_box)
        tag_layout.setContentsMargins(4, 8, 4, 4)
        tag_layout.setSpacing(4)
        self.tag_list_widget = QListWidget()
        self.tag_list_widget.setObjectName("TagList")
        self.tag_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection) # Changed back
        self.tag_list_widget.itemClicked.connect(self._on_tag_item_clicked) # Use itemClicked again
        tag_layout.addWidget(self.tag_list_widget)
        self.list_tag_splitter.addWidget(self.tag_group_box)

        sidebar_layout.addWidget(self.list_tag_splitter, 1)

        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.new_note_btn = QPushButton(get_icon("new_note.png", QStyle.StandardPixmap.SP_FileIcon), "New Note")
        self.new_note_btn.setToolTip("Create a new note (Ctrl+N)")
        self.new_note_btn.setShortcut(QKeySequence("Ctrl+N"))
        self.new_note_btn.clicked.connect(self._create_new_note)
        self.new_snippet_btn = QPushButton(get_icon("new_snippet.png", QStyle.StandardPixmap.SP_FileDialogNewFolder), "New Snippet")
        self.new_snippet_btn.setToolTip("Create a new code snippet (Ctrl+Shift+N)")
        self.new_snippet_btn.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.new_snippet_btn.clicked.connect(self._create_new_snippet)
        self.clear_tag_filter_btn = QPushButton(get_icon("clear_filter.png", QStyle.StandardPixmap.SP_DialogCancelButton), "Clear")
        self.clear_tag_filter_btn.setToolTip("Clear tag selection (Shift+Ctrl+C)")
        self.clear_tag_filter_btn.clicked.connect(self._clear_tag_filter)
        self.clear_tag_filter_btn.setEnabled(False)
        control_buttons_layout.addWidget(self.new_note_btn)
        control_buttons_layout.addWidget(self.new_snippet_btn)
        control_buttons_layout.addWidget(self.clear_tag_filter_btn)
        control_buttons_layout.addStretch(1)
        sidebar_layout.addLayout(control_buttons_layout)

        self.content_area = QTabWidget()
        self.content_area.setTabsClosable(True)
        self.content_area.tabCloseRequested.connect(self._close_tab_request)
        self.content_area.setMovable(True)

        self.status_bar = self.statusBar()
        self.db_error_label = QLabel("")
        self.db_error_label.setStyleSheet("color: red;")
        self.status_bar.addPermanentWidget(self.db_error_label)

        self.main_splitter.addWidget(sidebar)
        self.main_splitter.addWidget(self.content_area)
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)
        main_layout.addWidget(self.main_splitter)

    def _open_donate_link(self):
        url = QUrl("https://www.paypal.com/paypalme/kh1512")
        print(f"Opening donate link: {url.toString()}")
        if not QDesktopServices.openUrl(url):
             QMessageBox.warning(self, "Error", "Could not open donation link in browser.")

    def _on_save_geometry_changed(self, state: int):
        should_save = state == Qt.CheckState.Checked.value
        print(f"Setting 'save_window_geometry' to: {should_save}")
        self.settings["save_window_geometry"] = should_save

    def _on_theme_changed(self, text: str):
        selected_theme_name = self.theme_combo.currentData()
        if selected_theme_name and selected_theme_name != self.settings.get("theme"):
            print(f"Theme selection changed to: {selected_theme_name}")
            self.settings["theme"] = selected_theme_name
            QMessageBox.information(self, "Theme Changed", "The theme will be applied the next time you start the application.")

    def _restore_geometry_and_state(self):
        print("Attempting to restore geometry and state...")
        use_defaults = True
        if self.settings.get("save_window_geometry", True):
            geom = self.settings.get("window_geometry"); maximized = self.settings.get("window_maximized", False)
            main_split_sizes = self.settings.get("main_splitter_sizes"); side_split_sizes = self.settings.get("sidebar_splitter_sizes")
            if maximized: print("Window was maximized, restoring maximized state."); QTimer.singleShot(0, self.showMaximized); use_defaults = False
            elif isinstance(geom, dict):
                x = geom.get("x"); y = geom.get("y"); w = geom.get("width"); h = geom.get("height")
                if all(v is not None and isinstance(v, (int, float)) and v >= 0 for v in [x, y, w, h]): print(f"Restoring geometry: x={x}, y={y}, w={w}, h={h}"); self.setGeometry(int(x), int(y), int(w), int(h)); use_defaults = False
                else: print("Saved geometry values invalid or incomplete.")
            else: print("No saved geometry found or format incorrect.")
            if isinstance(main_split_sizes, list) and len(main_split_sizes) == 2 and hasattr(self, 'main_splitter'):
                try: self.main_splitter.setSizes([int(s) for s in main_split_sizes]); print(f"Restored main splitter sizes: {main_split_sizes}")
                except: print(f"Error restoring main splitter sizes. Using defaults."); self.main_splitter.setSizes([300, 900])
            elif hasattr(self, 'main_splitter'): self.main_splitter.setSizes([300, 900])
            if isinstance(side_split_sizes, list) and len(side_split_sizes) == 2 and hasattr(self, 'list_tag_splitter'):
                try: self.list_tag_splitter.setSizes([int(s) for s in side_split_sizes]); print(f"Restored sidebar splitter sizes: {side_split_sizes}")
                except: print(f"Error restoring sidebar splitter sizes. Using defaults."); self.list_tag_splitter.setSizes([400, 200])
            elif hasattr(self, 'list_tag_splitter'): self.list_tag_splitter.setSizes([400, 200])
        if use_defaults:
             print("Using default window size and maximizing."); QTimer.singleShot(0, self.showMaximized)
             if hasattr(self, 'main_splitter'): self.main_splitter.setSizes([300, 900])
             if hasattr(self, 'list_tag_splitter'): self.list_tag_splitter.setSizes([400, 200])

    def _setup_shortcuts(self):
        close_tab_action = QAction("Close Tab", self); close_tab_action.setShortcut(QKeySequence("Ctrl+W")); close_tab_action.triggered.connect(self._close_current_tab_slot); self.addAction(close_tab_action)
        clear_filter_action = QAction("Clear Tag Filter", self); clear_filter_action.setShortcut(QKeySequence("Shift+Ctrl+C")); clear_filter_action.triggered.connect(self._clear_tag_filter); self.addAction(clear_filter_action)

    def _close_current_tab_slot(self):
        current_index = self.content_area.currentIndex()
        if current_index != -1:
            self._close_tab_request(current_index)

    def _close_tab_request(self, index):
        widget = self.content_area.widget(index)
        if not isinstance(widget, (NoteEditor, SnippetEditor)): print(f"Attempting to close non-editor tab at index {index}."); self.content_area.removeTab(index); return
        if widget.is_dirty():
            tab_text = self.content_area.tabText(index).rstrip("*")
            reply = QMessageBox.question(self, "Save Changes?",f"'{tab_text}' has unsaved changes.\nDo you want to save them?", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save: widget.save_changes(); self.content_area.removeTab(index)
            elif reply == QMessageBox.StandardButton.Discard: self.content_area.removeTab(index)
        else: self.content_area.removeTab(index)

    def _reload_all_data(self, refresh_tags=False):
        filter_list = self._current_tag_filter # Pass string or None
        print(f"Reloading data. Current tag filter: {filter_list}")
        search_query = self.search_input.text()
        if search_query:
            self.data_manager.search_notes_async(search_query, filter_list)
            self.data_manager.search_snippets_async(search_query, filter_list)
        else:
            self.data_manager.load_all_notes_async(filter_list)
            self.data_manager.load_all_snippets_async(filter_list)
        if refresh_tags:
            self._refresh_tag_list()

    def _trigger_search(self):
        if self._is_closing: return
        self._reload_all_data(refresh_tags=False)

    def _refresh_tag_list(self):
        if not self._is_closing:
             print("Requesting tag list refresh.")
             self.data_manager.load_all_tags_async()

    def _handle_all_tags_loaded(self, tags: List[str]):
        if self._is_closing: return
        print(f"Updating tag list widget with {len(tags)} tags.")
        selected_tag_text = self._current_tag_filter
        self.tag_list_widget.blockSignals(True)
        self.tag_list_widget.clear()
        self.tag_list_widget.addItems(tags)
        item_was_selected = False
        if selected_tag_text:
            for i in range(self.tag_list_widget.count()):
                item = self.tag_list_widget.item(i)
                if item.text() == selected_tag_text:
                    self.tag_list_widget.setCurrentItem(item)
                    item_was_selected = True
                    break
            if not item_was_selected:
                self._current_tag_filter = None # Clear filter if tag disappeared
        self.tag_list_widget.blockSignals(False)
        self.clear_tag_filter_btn.setEnabled(item_was_selected)

    def _on_tag_item_clicked(self, item: QListWidgetItem):
        if item is None: return
        selected_tag = item.text()
        if self._current_tag_filter == selected_tag:
            # Clicked current tag: Clear filter
            self._clear_tag_filter()
            # Deselect visually
            self.tag_list_widget.blockSignals(True)
            self.tag_list_widget.clearSelection()
            self.tag_list_widget.setCurrentItem(None)
            self.tag_list_widget.blockSignals(False)
        else:
            # Clicked new tag: Apply filter
            new_filter = selected_tag
            if new_filter != self._current_tag_filter:
                self._current_tag_filter = new_filter
                print(f"Tag filter changed to: {self._current_tag_filter}")
                self.clear_tag_filter_btn.setEnabled(True)
                self._reload_all_data(refresh_tags=False)
            self.tag_list_widget.setCurrentItem(item)
            self.clear_tag_filter_btn.setEnabled(True)

    # --- REMOVED _on_tag_selection_changed ---

    def _clear_tag_filter(self):
        if not self._current_tag_filter: print("Clear tag filter called, but no filter was active."); return
        print("Clearing tag filter.")
        self._current_tag_filter = None
        self.tag_list_widget.blockSignals(True); self.tag_list_widget.clearSelection(); self.tag_list_widget.setCurrentItem(None); self.tag_list_widget.blockSignals(False)
        self.clear_tag_filter_btn.setEnabled(False)
        self._reload_all_data(refresh_tags=False)

    def _create_new_note(self):
        editor = NoteEditor(data_manager=self.data_manager, settings=self.settings)
        self._connect_editor_signals(editor)
        idx = self.content_area.addTab(editor, "New Note*")
        self.content_area.setCurrentIndex(idx)

    def _create_new_snippet(self):
        editor = SnippetEditor(data_manager=self.data_manager)
        self._connect_editor_signals(editor)
        idx = self.content_area.addTab(editor, "New Snippet*")
        self.content_area.setCurrentIndex(idx)

    def _open_editor_tab(self, editor_type: str, item_data: Any):
        if not hasattr(item_data, 'id'): print(f"Error: Item data for {editor_type} lacks an 'id' attribute."); return
        item_id=item_data.id; editor_class=NoteEditor if editor_type=='note' else SnippetEditor
        for i in range(self.content_area.count()):
            widget=self.content_area.widget(i)
            if isinstance(widget, editor_class) and widget.get_object_id()==item_id:
                self.content_area.setCurrentIndex(i)
                return
        db_data = None
        if editor_type=='note': db_data = self.data_manager.get_note_sync(item_id)
        elif editor_type=='snippet': db_data = self.data_manager.get_snippet_sync(item_id)
        if db_data:
            editor_kwargs={'data_manager': self.data_manager}
            if editor_type == 'note':
                 editor_kwargs['note_data'] = db_data
                 editor_kwargs['settings'] = self.settings
            else:
                 editor_kwargs['snippet_data'] = db_data
            editor=editor_class(**editor_kwargs)
            self._connect_editor_signals(editor)
            idx=self.content_area.addTab(editor, db_data.title or f"Untitled {editor_type.capitalize()}")
            self.content_area.setCurrentIndex(idx)
        else:
            QMessageBox.warning(self, "Error", f"Could not load {editor_type} with ID {item_id}.")

    def _on_note_selected(self, item: NoteItem):
        if item and hasattr(item, 'data_object'): self._open_editor_tab('note', item.data_object)

    def _on_snippet_selected(self, item: SnippetItem):
        if item and hasattr(item, 'data_object'): self._open_editor_tab('snippet', item.data_object)

    def _connect_editor_signals(self, editor):
        editor.saveRequested.connect(self._handle_save_requested)
        editor.deleteRequested.connect(self._handle_delete_requested)
        editor.dirtyChanged.connect(self._handle_dirty_changed)
        if isinstance(editor, NoteEditor): editor.note_saved.connect(self._update_note_list_item); editor.note_deleted.connect(self._remove_note_list_item_and_tab)
        elif isinstance(editor, SnippetEditor): editor.snippet_saved.connect(self._update_snippet_list_item); editor.snippet_deleted.connect(self._remove_snippet_list_item_and_tab)
        connection_type=Qt.ConnectionType.QueuedConnection
        if isinstance(editor, NoteEditor):
             self.data_manager.note_added.connect(lambda note, ed=editor: ed.handle_save_success(note) if ed and not ed.isHidden() and not self._is_closing and ed.is_new and note.id is not None else None, connection_type)
             self.data_manager.note_updated.connect(lambda note, ed=editor: ed.handle_save_success(note) if ed and not ed.isHidden() and not self._is_closing and note.id == ed.get_object_id() else None, connection_type)
             self.data_manager.note_deleted.connect(lambda note_id, ed=editor: ed.handle_delete_success() if ed and not ed.isHidden() and not self._is_closing and note_id == ed.get_object_id() else None, connection_type)
             self.data_manager.db_error.connect(lambda task_id, error_msg, ed=editor: ed.handle_db_error(error_msg) if ed and not ed.isHidden() else None, connection_type)
        elif isinstance(editor, SnippetEditor):
             self.data_manager.snippet_added.connect(lambda snippet, ed=editor: ed.handle_save_success(snippet) if ed and not ed.isHidden() and not self._is_closing and ed.is_new and snippet.id is not None else None, connection_type)
             self.data_manager.snippet_updated.connect(lambda snippet, ed=editor: ed.handle_save_success(snippet) if ed and not ed.isHidden() and not self._is_closing and snippet.id == ed.get_object_id() else None, connection_type)
             self.data_manager.snippet_deleted.connect(lambda snippet_id, ed=editor: ed.handle_delete_success() if ed and not ed.isHidden() and not self._is_closing and snippet_id == ed.get_object_id() else None, connection_type)
             self.data_manager.db_error.connect(lambda task_id, error_msg, ed=editor: ed.handle_db_error(error_msg) if ed and not ed.isHidden() else None, connection_type)

    # --- Handlers - Corrected Indentation ---
    def _handle_all_notes_loaded(self, notes: list[Note]):
        if self._is_closing: return
        print(f"Notes loaded (Filter: {self._current_tag_filter}). Updating list.")
        self.notes_list.clear()
        for note in notes:
            item = NoteItem(note)
            self.notes_list.addItem(item)
            # Corrected Indentation
            if hasattr(item, 'widget') and item.widget:
                self.notes_list.setItemWidget(item, item.widget)

    def _handle_note_added(self, note: Note):
        if self._is_closing: return
        print(f"Note added: ID={note.id}.")
        # Update list only if it matches current filter
        if self._current_tag_filter is None or self._current_tag_filter in (note.tags or "").split(','):
             self._update_note_list_item(note)
        # Refresh tags via signal tags_updated handled in connect_signals

    def _handle_note_updated(self, note: Note):
        if self._is_closing: return
        print(f"Note updated: ID={note.id}.")
        # Check if the updated note *still* matches the filter
        matches_filter = self._current_tag_filter is None or self._current_tag_filter in (note.tags or "").split(',')
        existing_item = self._find_list_item(self.notes_list, NoteItem, note.id)
        if matches_filter:
            self._update_note_list_item(note) # Update or add if it matches now
        elif existing_item:
            # If it existed but no longer matches, remove it
            row = self.notes_list.row(existing_item)
            self.notes_list.takeItem(row)
            print(f"Removed note {note.id} from list because it no longer matches filter '{self._current_tag_filter}'.")
        # Refresh tags via signal tags_updated handled in connect_signals

    def _handle_note_deleted(self, note_id: int):
        if self._is_closing: return
        print(f"Note deleted: ID={note_id}.")
        self._remove_note_list_item_and_tab(note_id)
        # Refresh tags via signal tags_updated handled in connect_signals

    def _handle_all_snippets_loaded(self, snippets: list[Snippet]):
        if self._is_closing: return
        print(f"Snippets loaded (Filter: {self._current_tag_filter}). Updating list.")
        self.snippets_list.clear()
        for snippet in snippets:
            item = SnippetItem(snippet)
            self.snippets_list.addItem(item)
            # Corrected Indentation
            if hasattr(item, 'widget') and item.widget:
                self.snippets_list.setItemWidget(item, item.widget)

    def _handle_snippet_added(self, snippet: Snippet):
        if self._is_closing: return
        print(f"Snippet added: ID={snippet.id}.")
        if self._current_tag_filter is None or self._current_tag_filter in (snippet.tags or "").split(','):
            self._update_snippet_list_item(snippet)
        # Refresh tags via signal tags_updated handled in connect_signals

    def _handle_snippet_updated(self, snippet: Snippet):
        if self._is_closing: return
        print(f"Snippet updated: ID={snippet.id}.")
        matches_filter = self._current_tag_filter is None or self._current_tag_filter in (snippet.tags or "").split(',')
        existing_item = self._find_list_item(self.snippets_list, SnippetItem, snippet.id)
        if matches_filter:
            self._update_snippet_list_item(snippet)
        elif existing_item:
             row = self.snippets_list.row(existing_item)
             self.snippets_list.takeItem(row)
             print(f"Removed snippet {snippet.id} from list because it no longer matches filter '{self._current_tag_filter}'.")
        # Refresh tags via signal tags_updated handled in connect_signals

    def _handle_snippet_deleted(self, snippet_id: int):
        if self._is_closing: return
        print(f"Snippet deleted: ID={snippet_id}.")
        self._remove_snippet_list_item_and_tab(snippet_id)
        # Refresh tags via signal tags_updated handled in connect_signals

    def _handle_note_searched(self, notes: list[Note]):
        if self._is_closing: return
        print(f"Note search results (Filter: {self._current_tag_filter}).")
        self.notes_list.clear()
        for note in notes:
            item = NoteItem(note)
            self.notes_list.addItem(item)
            # Corrected Indentation
            if hasattr(item, 'widget') and item.widget:
                self.notes_list.setItemWidget(item, item.widget)

    def _handle_snippet_searched(self, snippets: list[Snippet]):
        if self._is_closing: return
        print(f"Snippet search results (Filter: {self._current_tag_filter}).")
        self.snippets_list.clear()
        for snippet in snippets:
            item = SnippetItem(snippet)
            self.snippets_list.addItem(item)
            # Corrected Indentation
            if hasattr(item, 'widget') and item.widget:
                self.snippets_list.setItemWidget(item, item.widget)

    def _handle_db_error(self, task_id: str, error_message: str):
        print(f"DB Error (Task '{task_id}'): {error_message}")
        if hasattr(self, 'db_error_label') and self.db_error_label:
            self.db_error_label.setText(f"DB Error: {error_message[:100]}...")
            QTimer.singleShot(7000, lambda: self.db_error_label.setText("") if self.db_error_label else None)

    def _handle_save_requested(self, editor: QObject, save_data: dict):
        print(f"Save requested from editor (ID: {save_data.get('id', 'New')}). Type: {save_data.get('editor_type')}")
        editor_type=save_data.get('editor_type'); obj_id=save_data.get('id'); title=save_data.get('title'); tags=save_data.get('tags'); specific_data=save_data.get('specific_data'); is_new=save_data.get('is_new')
        if editor_type=='note': note=Note(id=obj_id, title=title, tags=tags, content=specific_data); (self.data_manager.add_note_async if is_new else self.data_manager.update_note_async)(note)
        elif editor_type=='snippet': code, language = specific_data; snippet=Snippet(id=obj_id, title=title, tags=tags, code=code, language=language); (self.data_manager.add_snippet_async if is_new else self.data_manager.update_snippet_async)(snippet)

    def _handle_delete_requested(self, editor: QObject, object_id: int):
        print(f"Delete requested from editor for ID: {object_id}.")
        if hasattr(editor, 'editor_type'):
            if editor.editor_type=='note': self.data_manager.delete_note_async(object_id)
            elif editor.editor_type=='snippet': self.data_manager.delete_snippet_async(object_id)
        else: print(f"Error: Cannot determine editor type for delete request.")

    def _handle_dirty_changed(self, is_dirty: bool):
        editor=self.sender(); index=self.content_area.indexOf(editor)
        if index == -1: return
        current_text=self.content_area.tabText(index)
        base_title="New Note" if isinstance(editor,NoteEditor) and editor.is_new else "New Snippet" if isinstance(editor,SnippetEditor) and editor.is_new else getattr(editor.object_data, 'title', '') if editor.object_data else current_text.rstrip("*")
        clean_text=base_title or (f"Untitled {editor.editor_type.capitalize()}" if editor.is_new else "Untitled")
        if is_dirty:
            if not current_text.endswith("*"): self.content_area.setTabText(index, clean_text + "*")
        else: new_title = getattr(editor.object_data, 'title', clean_text) if editor.object_data else clean_text; self.content_area.setTabText(index, new_title)

    def _find_list_item(self, list_widget: QListWidget, item_class: type, item_id: int) -> Optional[QListWidgetItem]:
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if isinstance(item, item_class) and hasattr(item, 'data_object') and getattr(item.data_object, 'id', None) == item_id:
                return item
        return None

    def _update_note_list_item(self, note: Note):
        if self._is_closing: return
        item_to_update = self._find_list_item(self.notes_list, NoteItem, note.id)
        row = -1
        if item_to_update:
             row = self.notes_list.row(item_to_update)
             self.notes_list.setItemWidget(item_to_update, None)
             self.notes_list.takeItem(row)
        new_item = NoteItem(note)
        self.notes_list.insertItem(0, new_item)
        # Corrected Indentation
        if hasattr(new_item, 'widget') and new_item.widget:
             self.notes_list.setItemWidget(new_item, new_item.widget)

    def _remove_note_list_item_and_tab(self, note_id: int):
        if self._is_closing: return
        item_to_remove = self._find_list_item(self.notes_list, NoteItem, note_id)
        if item_to_remove:
            row = self.notes_list.row(item_to_remove)
            self.notes_list.setItemWidget(item_to_remove, None)
            self.notes_list.takeItem(row)
            print(f"Removed note {note_id} from list.")
        for i in range(self.content_area.count()):
            widget = self.content_area.widget(i)
            if isinstance(widget, NoteEditor) and widget.get_object_id() == note_id:
                self.content_area.removeTab(i)
                break

    def _update_snippet_list_item(self, snippet: Snippet):
        if self._is_closing: return
        item_to_update = self._find_list_item(self.snippets_list, SnippetItem, snippet.id)
        row = -1
        if item_to_update:
            row = self.snippets_list.row(item_to_update)
            self.snippets_list.setItemWidget(item_to_update, None)
            self.snippets_list.takeItem(row)
        new_item = SnippetItem(snippet)
        self.snippets_list.insertItem(0, new_item)
        # Corrected Indentation
        if hasattr(new_item, 'widget') and new_item.widget:
            self.snippets_list.setItemWidget(new_item, new_item.widget)

    def _remove_snippet_list_item_and_tab(self, snippet_id: int):
        if self._is_closing: return
        item_to_remove = self._find_list_item(self.snippets_list, SnippetItem, snippet_id)
        if item_to_remove:
            row = self.snippets_list.row(item_to_remove)
            self.snippets_list.setItemWidget(item_to_remove, None)
            self.snippets_list.takeItem(row)
            print(f"Removed snippet {snippet_id} from list.")
        for i in range(self.content_area.count()):
            widget = self.content_area.widget(i)
            if isinstance(widget, SnippetEditor) and widget.get_object_id() == snippet_id:
                self.content_area.removeTab(i)
                break

    def _close_tab_request(self, index):
        widget = self.content_area.widget(index)
        if not isinstance(widget, (NoteEditor, SnippetEditor)):
            print(f"Attempting to close non-editor tab at index {index}.")
            self.content_area.removeTab(index)
            return
        if widget.is_dirty():
            tab_text = self.content_area.tabText(index).rstrip("*")
            reply = QMessageBox.question(self, "Save Changes?",f"'{tab_text}' has unsaved changes.\nDo you want to save them?", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save:
                widget.save_changes()
                self.content_area.removeTab(index)
            elif reply == QMessageBox.StandardButton.Discard:
                self.content_area.removeTab(index)
        else:
            self.content_area.removeTab(index)

    def closeEvent(self, event):
        print("Main window close event triggered.")
        dirty_tabs_indices=[]
        for i in reversed(range(self.content_area.count())):
            widget=self.content_area.widget(i)
            if isinstance(widget, (NoteEditor, SnippetEditor)) and widget.is_dirty():
                dirty_tabs_indices.append(i)
        if not dirty_tabs_indices:
            print("No dirty editor tabs found. Setting closing flag and accepting event.")
            self._is_closing = True
            event.accept()
            return
        print(f"Found dirty editor tabs at indices: {dirty_tabs_indices}. Prompting user...")
        for index in dirty_tabs_indices:
            if index >= self.content_area.count():
                continue
            widget = self.content_area.widget(index)
            if not isinstance(widget, (NoteEditor, SnippetEditor)) or not widget.is_dirty():
                continue
            self.content_area.setCurrentIndex(index)
            tab_text=self.content_area.tabText(index).rstrip("*")
            reply = QMessageBox.question(self, "Save Changes Before Closing?",
                                         f"'{tab_text}' has unsaved changes.\nDo you want to save them?",
                                         QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save:
                print(f"User chose SAVE for tab {index} during window close.")
                widget.save_changes()
            elif reply == QMessageBox.StandardButton.Discard:
                print(f"User chose DISCARD for tab {index} during window close.")
            else: # Cancel
                print(f"User chose CANCEL for tab {index} during window close. Aborting window close.")
                event.ignore()
                return
        print("All dirty editor tabs handled. Setting closing flag and accepting event.")
        self._is_closing = True
        event.accept()


# ui/main_window.py
# --- END OF FILE ui/main_window.py ---