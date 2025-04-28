# ui/syntax_highlighter.py
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor, QTextDocument
from PyQt6.QtCore import QRegularExpression, Qt

class SyntaxHighlighter(QSyntaxHighlighter):
    """
    Custom syntax highlighter for various languages in a QTextDocument.
    Supports Python, JavaScript, HTML, CSS, SQL, and basic highlighting for others.
    """

    def __init__(self, parent: QTextDocument = None, language: str = "python"):
        super().__init__(parent)
        self.language = "" # Will be set by set_language
        self.highlighting_rules = []

        # Common formats
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor(197, 134, 192)) # Purple
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor(229, 192, 123)) # Yellow/Gold

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor(255, 170, 0)) # Orange

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor(152, 195, 121)) # Green

        self.singleline_comment_format = QTextCharFormat()
        self.singleline_comment_format.setForeground(QColor(128, 128, 128)) # Grey
        self.singleline_comment_format.setFontItalic(True)

        self.multiline_comment_format = QTextCharFormat()
        self.multiline_comment_format.setForeground(QColor(128, 128, 128)) # Grey
        self.multiline_comment_format.setFontItalic(True)

        self.html_tag_format = QTextCharFormat()
        self.html_tag_format.setForeground(QColor(86, 156, 214)) # Blue
        self.html_attr_format = QTextCharFormat()
        self.html_attr_format.setForeground(QColor(156, 220, 254)) # Light Blue
        self.html_value_format = QTextCharFormat()
        self.html_value_format.setForeground(QColor(152, 195, 121)) # Green (like strings)

        self.css_selector_format = QTextCharFormat()
        self.css_selector_format.setForeground(QColor(215, 186, 125)) # Tan/Brown
        self.css_property_format = QTextCharFormat()
        self.css_property_format.setForeground(QColor(156, 220, 254)) # Light Blue
        self.css_value_format = QTextCharFormat()
        self.css_value_format.setForeground(QColor(184, 115, 211)) # Light Purple

        # Multi-line comment delimiters
        self.comment_start = None
        self.comment_end = None
        self.singleline_comment_pattern = None

        self.set_language(language) # Initialize rules

    def set_language(self, language: str):
        """Sets the language for syntax highlighting and rebuilds rules."""
        new_lang = language.lower().strip()
        if new_lang == self.language:
            return # No change needed

        self.language = new_lang
        self.highlighting_rules.clear()
        self.comment_start = None
        self.comment_end = None
        self.singleline_comment_pattern = None

        print(f"SyntaxHighlighter: Setting language to '{self.language}'") # Debug print

        # Always add common rules first (can be overridden by specific language rules)
        self._add_common_rules()

        # Add language-specific rules
        if self.language == "python": self._setup_python_rules()
        elif self.language == "javascript": self._setup_javascript_rules()
        elif self.language == "html": self._setup_html_rules()
        elif self.language == "css": self._setup_css_rules()
        elif self.language == "sql": self._setup_sql_rules()
        elif self.language in ["java", "c++", "c#", "php", "ruby", "go"]:
             self._setup_generic_c_style_rules() # Use common rules for these
        # Default: Only common rules (numbers, strings) and no comments for "Text" or unknown

        self.rehighlight() # Re-apply highlighting to the entire document

    def _add_common_rules(self):
        """Adds rules common to most languages (numbers, strings)."""
        # Numbers (integers and floats)
        self.highlighting_rules.append(
            (QRegularExpression(r"\b\d+(\.\d+)?([eE][+-]?\d+)?\b"), self.number_format)
        )
        # Strings (double and single quoted)
        self.highlighting_rules.extend([
            (QRegularExpression(r'"(?:\\.|[^"\\])*"'), self.string_format),
            (QRegularExpression(r"'(?:\\.|[^'\\])*'"), self.string_format)
        ])

    def _add_keywords(self, keywords: list[str]):
        """Helper to add keyword highlighting rules."""
        for keyword in keywords:
            # Use word boundaries to avoid matching parts of words
            pattern = QRegularExpression(r'\b' + keyword + r'\b')
            self.highlighting_rules.append((pattern, self.keyword_format))

    def _add_builtins(self, builtins: list[str]):
        """Helper to add built-in function/type highlighting rules."""
        for builtin in builtins:
            pattern = QRegularExpression(r'\b' + builtin + r'\b')
            self.highlighting_rules.append((pattern, self.builtin_format))

    def _setup_python_rules(self):
        python_keywords = [
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
            'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
            'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
            'try', 'while', 'with', 'yield', 'match', 'case' # Added match/case
        ]
        self._add_keywords(python_keywords)

        python_builtins = [
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
            'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
            'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec',
            'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
            'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow',
            'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',
            'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
            'tuple', 'type', 'vars', 'zip', '__import__'
        ]
        self._add_builtins(python_builtins)

        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor(220, 220, 170)) # Light yellow
        self.highlighting_rules.append((QRegularExpression(r"@[a-zA-Z_][a-zA-Z0-9_]*"), decorator_format))

        # self keyword
        self_format = QTextCharFormat()
        self_format.setForeground(QColor(86, 156, 214)) # Blue
        self.highlighting_rules.append((QRegularExpression(r"\bself\b"), self_format))

        # Triple-quoted strings (multi-line handled separately)
        self.highlighting_rules.extend([
            (QRegularExpression(r'"""(?:\\.|[^"\\])*"""'), self.string_format),
            (QRegularExpression(r"'''(?:\\.|[^'\\])*'''"), self.string_format)
        ])

        self.singleline_comment_pattern = QRegularExpression(r'#.*$')
        self.comment_start = QRegularExpression(r'"""|\'\'\'')
        self.comment_end = QRegularExpression(r'"""|\'\'\'') # Python uses same delimiter

    def _setup_javascript_rules(self):
        js_keywords = [
            'break', 'case', 'catch', 'class', 'const', 'continue', 'debugger',
            'default', 'delete', 'do', 'else', 'export', 'extends', 'finally',
            'for', 'function', 'if', 'import', 'in', 'instanceof', 'new',
            'return', 'super', 'switch', 'this', 'throw', 'try', 'typeof',
            'var', 'void', 'while', 'with', 'yield', 'let', 'static', 'async', 'await',
            'get', 'set' # Added get/set
        ]
        self._add_keywords(js_keywords)

        js_builtins = [ # Examples
             'Array', 'Boolean', 'Date', 'Error', 'EvalError', 'Function', 'Infinity',
             'JSON', 'Math', 'NaN', 'Number', 'Object', 'Promise', 'Proxy', 'RangeError',
             'ReferenceError', 'RegExp', 'Set', 'String', 'Symbol', 'SyntaxError',
             'TypeError', 'URIError', 'Uint8Array', 'Map', 'WeakMap', 'WeakSet',
             'console', 'decodeURI', 'decodeURIComponent', 'document', 'encodeURI',
             'encodeURIComponent', 'eval', 'isFinite', 'isNaN', 'null', 'parseFloat',
             'parseInt', 'undefined', 'window', 'globalThis', 'arguments' # Added more
        ]
        self._add_builtins(js_builtins)

        # Boolean literals
        bool_format = QTextCharFormat()
        bool_format.setForeground(QColor(86, 156, 214)) # Blue
        self.highlighting_rules.append((QRegularExpression(r"\b(true|false)\b"), bool_format))

        # Template literals (basic highlighting)
        template_literal_format = QTextCharFormat()
        template_literal_format.setForeground(QColor(206, 145, 120)) # Brown/Orange
        self.highlighting_rules.append((QRegularExpression(r"`(?:\\.|[^`])*`"), template_literal_format))

        self.singleline_comment_pattern = QRegularExpression(r'//.*$')
        self.comment_start = QRegularExpression(r'/\*')
        self.comment_end = QRegularExpression(r'\*/')

    def _setup_html_rules(self):
         # Basic HTML tags <...>
         self.highlighting_rules.append((QRegularExpression(r"</?\s*([a-zA-Z0-9\-\:]+)[^>]*>"), self.html_tag_format))
         # Attributes (e.g., class=...) - simple match
         self.highlighting_rules.append((QRegularExpression(r"\b([a-zA-Z\-]+)\s*="), self.html_attr_format))
         # Values in quotes are handled by common string rules
         # Doctype
         doctype_format = QTextCharFormat()
         doctype_format.setForeground(QColor(128, 128, 128)) # Grey
         self.highlighting_rules.append((QRegularExpression(r"<!DOCTYPE[^>]*>"), doctype_format))

         self.comment_start = QRegularExpression(r"<!--")
         self.comment_end = QRegularExpression(r"-->")
         self.singleline_comment_pattern = None

    def _setup_css_rules(self):
         # Selectors (IDs, classes, tags, pseudo-classes) - Simplified
         self.highlighting_rules.append((QRegularExpression(r"(^|[,{\s])([#.]?[a-zA-Z][a-zA-Z0-9\-_]*|[*])"), self.css_selector_format)) # Basic class/id/tag/universal
         self.highlighting_rules.append((QRegularExpression(r":[a-zA-Z\-]+"), self.css_selector_format)) # Pseudo classes/elements

         # Properties (e.g., color:)
         self.highlighting_rules.append((QRegularExpression(r"\b([a-zA-Z\-]+)\s*:"), self.css_property_format))

         # Values - includes hex colors, numbers with units, keywords
         self.highlighting_rules.append((QRegularExpression(r":\s*(#[0-9a-fA-F]{3,8}|rgb[a]?\(.*?\)|hsl[a]?\(.*?\)|[-\w]+|\d+(\.\d+)?(px|em|rem|%|pt|vh|vw)?)\b"), self.css_value_format))
         # Strings are handled by common rules
         # Numbers are partially handled by common rules, unit handling is basic here

         self.comment_start = QRegularExpression(r'/\*')
         self.comment_end = QRegularExpression(r'\*/')
         self.singleline_comment_pattern = None # CSS uses block comments

    def _setup_sql_rules(self):
        sql_keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET',
            'DELETE', 'CREATE', 'TABLE', 'INDEX', 'VIEW', 'DATABASE', 'ALTER', 'DROP',
            'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT', 'BEGIN', 'TRANSACTION',
            'END', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'GROUP', 'BY',
            'ORDER', 'ASC', 'DESC', 'LIMIT', 'OFFSET', 'HAVING', 'AS', 'DISTINCT',
            'UNION', 'ALL', 'CASE', 'WHEN', 'THEN', 'ELSE', 'AND', 'OR', 'NOT', 'IN',
            'LIKE', 'BETWEEN', 'IS', 'NULL', 'EXISTS', 'PRIMARY', 'KEY', 'FOREIGN',
            'REFERENCES', 'UNIQUE', 'CHECK', 'DEFAULT', 'CONSTRAINT', 'VARCHAR', 'INT',
            'INTEGER', 'TEXT', 'BLOB', 'REAL', 'FLOAT', 'DATE', 'DATETIME', 'TIMESTAMP',
            'BOOLEAN', 'TRUE', 'FALSE'
        ]
        self._add_keywords(sql_keywords)

        sql_functions = [ # Common examples
             'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ABS', 'ROUND', 'UPPER', 'LOWER',
             'SUBSTR', 'SUBSTRING', 'LENGTH', 'CAST', 'COALESCE', 'NULLIF', 'DATE',
             'TIME', 'DATETIME', 'STRFTIME', 'RANDOM'
        ]
        self._add_builtins(sql_functions) # Use builtin format for functions

        self.singleline_comment_pattern = QRegularExpression(r'--.*$')
        self.comment_start = QRegularExpression(r'/\*')
        self.comment_end = QRegularExpression(r'\*/')

    def _setup_generic_c_style_rules(self):
        """ Basic highlighting for C-style languages (Java, C++, C#, PHP etc.) """
        c_style_keywords = [ # Common subset
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'default', 'break',
            'continue', 'return', 'goto', 'try', 'catch', 'finally', 'throw', 'throws',
            'public', 'private', 'protected', 'static', 'final', 'abstract', 'class',
            'interface', 'enum', 'struct', 'namespace', 'using', 'import', 'package',
            'new', 'delete', 'this', 'super', 'extends', 'implements', 'virtual',
            'override', 'const', 'volatile', 'synchronized', 'transient', 'native',
            'void', 'int', 'long', 'float', 'double', 'char', 'byte', 'short', 'boolean',
            'string', 'var', 'let', 'auto' # Include common type keywords
        ]
        self._add_keywords(c_style_keywords)

        c_style_literals = ['true', 'false', 'null', 'nullptr', 'undefined']
        literal_format = QTextCharFormat()
        literal_format.setForeground(QColor(86, 156, 214)) # Blue
        for literal in c_style_literals:
             self.highlighting_rules.append((QRegularExpression(r"\b" + literal + r"\b"), literal_format))

        # Preprocessor directives (basic #...)
        preprocessor_format = QTextCharFormat()
        preprocessor_format.setForeground(QColor(155, 155, 155)) # Dark Grey
        self.highlighting_rules.append((QRegularExpression(r"^\s*#.*"), preprocessor_format))

        self.singleline_comment_pattern = QRegularExpression(r'//.*$')
        self.comment_start = QRegularExpression(r'/\*')
        self.comment_end = QRegularExpression(r'\*/')


    def highlightBlock(self, text: str):
        """Applies highlighting rules to the given text block."""

        # --- 1. Apply language-specific rules first ---
        for pattern, fmt in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                # Check if already formatted by multi-line comment state
                is_commented = False
                for i in range(match.capturedLength()):
                     if self.format(match.capturedStart() + i) == self.multiline_comment_format:
                         is_commented = True
                         break
                if not is_commented:
                     self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

        # --- 2. Handle multi-line comments ---
        current_block_state = 0 # 0 = normal, 1 = inside multi-line comment
        search_index = 0

        # Check previous block state
        previous_state = self.previousBlockState()
        if previous_state == 1 and self.comment_end:
            # Continuing a comment from the previous block
            end_match = self.comment_end.match(text, 0)
            if end_match.hasMatch():
                # Comment ends in this block
                end_offset = end_match.capturedStart() + end_match.capturedLength()
                self.setFormat(0, end_offset, self.multiline_comment_format)
                search_index = end_offset
                current_block_state = 0
            else:
                # Comment continues through this block
                self.setFormat(0, len(text), self.multiline_comment_format)
                current_block_state = 1
                self.setCurrentBlockState(current_block_state)
                return # Nothing else to format in this block
        else:
             current_block_state = 0 # Start in normal state


        # Find comment start/end within the rest of the block
        if self.comment_start and self.comment_end:
            while search_index < len(text):
                start_match = self.comment_start.match(text, search_index)
                if not start_match.hasMatch():
                    break # No more comment starts in this block

                start_offset = start_match.capturedStart()
                search_index = start_offset + start_match.capturedLength() # Start looking for end after start

                end_match = self.comment_end.match(text, search_index)
                if end_match.hasMatch():
                    # Comment starts and ends in this block
                    end_offset = end_match.capturedStart() + end_match.capturedLength()
                    self.setFormat(start_offset, end_offset - start_offset, self.multiline_comment_format)
                    search_index = end_offset
                    current_block_state = 0
                else:
                    # Comment starts but doesn't end in this block
                    self.setFormat(start_offset, len(text) - start_offset, self.multiline_comment_format)
                    current_block_state = 1
                    break # Stop searching this block

        # --- 3. Handle single-line comments ---
        # Apply *after* other rules and multi-line comments
        if self.singleline_comment_pattern and current_block_state == 0: # Only apply if not inside multi-line
             match_iterator = self.singleline_comment_pattern.globalMatch(text)
             while match_iterator.hasNext():
                 match = match_iterator.next()
                 # Check if the start of the match is inside a multi-line comment first
                 is_in_multiline = False
                 if self.format(match.capturedStart()) == self.multiline_comment_format:
                      is_in_multiline = True

                 if not is_in_multiline:
                      self.setFormat(match.capturedStart(), match.capturedLength(), self.singleline_comment_format)


        # --- Set the final state for the *next* block ---
        self.setCurrentBlockState(current_block_state)

# ui/syntax_highlighter.py
# --- END OF FILE syntax_highlighter.py ---
