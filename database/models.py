# --- START OF FILE database/models.py ---

# database/models.py
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Optional
import sqlite3

def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Safely parse ISO format datetime strings (potentially with Z or offset)."""
    if not dt_str:
        return None
    try:
        # Handle 'Z' timezone by replacing it with +00:00 which fromisoformat understands
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        # Let fromisoformat handle various valid ISO formats including offsets
        return datetime.fromisoformat(dt_str)
    except ValueError:
        # Fallback for common non-ISO formats if needed
        try:
            # Example: YYYY-MM-DD HH:MM:SS
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            print(f"Warning: Could not parse datetime string: '{dt_str}'")
            return None
    except Exception as e: # Catch any other unexpected error during parsing
        print(f"Warning: Unexpected error parsing datetime string '{dt_str}': {e}")
        return None


@dataclass
class Note:
    """Data model representing a Note."""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    tags: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> 'Note':
        """Creates a Note instance from a database row."""
        return cls(
            id=row['id'],
            title=row['title'] or "",
            content=row['content'] or "",
            tags=row['tags'] or "",
            created_at=_parse_datetime(row['created_at']),
            updated_at=_parse_datetime(row['updated_at'])
        )

@dataclass
class Snippet:
    """Data model representing a Code Snippet."""
    id: Optional[int] = None
    title: str = ""
    code: str = ""
    language: str = "Text" # Default to Text
    tags: str = ""
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> 'Snippet':
        """Creates a Snippet instance from a database row."""
        return cls(
            id=row['id'],
            title=row['title'] or "",
            code=row['code'] or "",
            language=row['language'] or "Text",
            tags=row['tags'] or "",
            created_at=_parse_datetime(row['created_at'])
        )

@dataclass
class RecentItem:
    """Data model representing a recent item (Note or Snippet)."""
    type: str # 'note' or 'snippet'
    id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None # For Notes
    last_activity_at: Optional[datetime] = None # Combined field for sorting

    @classmethod
    def from_db_row(cls, row: sqlite3.Row) -> 'RecentItem':
        """Creates a RecentItem instance from a combined database row."""
        return cls(
            type=row['type'],
            id=row['id'],
            title=row['title'] or "",
            created_at=_parse_datetime(row['created_at']),
            updated_at=_parse_datetime(row['updated_at']), # Will be None for snippets from query
            last_activity_at=_parse_datetime(row['last_activity_at'])
        )

# database/models.py
# --- END OF FILE database/models.py ---