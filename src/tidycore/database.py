"""Durable move journal and statistics derived from completed operations.

Connections are short lived, thread local to each call, and explicitly closed.
Filesystem and SQLite cannot share a transaction: pending rows bridge that gap.
"""
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
import sqlite3
import threading

from .utils import data_path

SCHEMA_VERSION = 2


class StatisticsDatabase:
    def __init__(self, db_path=None):
        self.db_path = str(db_path or data_path('tidycore_stats.db'))
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute('PRAGMA foreign_keys=ON')
            conn.execute('PRAGMA synchronous=FULL')
            with conn:
                yield conn
        finally:
            conn.close()

    def backup(self, destination=None):
        path = Path(destination or f'{self.db_path}.backup-{datetime.now():%Y%m%d-%H%M%S-%f}')
        with self.connection() as source:
            target = sqlite3.connect(path)
            try:
                source.backup(target)
            finally:
                target.close()
        return path

    def _init_database(self):
        with self.connection() as conn:
            if conn.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise sqlite3.DatabaseError('Database integrity check failed. Original retained; restore a verified backup.')
            version = conn.execute('PRAGMA user_version').fetchone()[0]
            if version > SCHEMA_VERSION:
                raise sqlite3.DatabaseError('Database was created by a newer TidyCore version.')
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE name='file_operations'").fetchone()
        if exists and version < SCHEMA_VERSION:
            self.backup()  # Never modify a legacy schema without a consistent SQLite backup.
        with self.connection() as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('BEGIN IMMEDIATE')
            conn.execute('''CREATE TABLE IF NOT EXISTS file_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL, source_path TEXT NOT NULL,
                destination_path TEXT NOT NULL, category TEXT NOT NULL,
                subcategory TEXT, operation_type TEXT DEFAULT 'organize',
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
            columns = {row['name'] for row in conn.execute('PRAGMA table_info(file_operations)')}
            for name, definition in {
                'status': "TEXT NOT NULL DEFAULT 'completed'",
                'operation_date': 'TEXT', 'fingerprint': 'TEXT',
                'error': 'TEXT', 'undone_at': 'TEXT',
            }.items():
                if name not in columns:
                    conn.execute(f'ALTER TABLE file_operations ADD COLUMN {name} {definition}')
            # Old timestamps were UTC, but daily aggregates used local dates. Preserve
            # original tables for inspection; new canonical counts use journal dates.
            conn.execute("UPDATE file_operations SET operation_date=date(timestamp,'localtime') WHERE operation_date IS NULL")
            conn.execute('CREATE INDEX IF NOT EXISTS operations_date_status ON file_operations(operation_date,status,category)')
            conn.execute('CREATE INDEX IF NOT EXISTS operations_status ON file_operations(status,id)')
            conn.execute('''CREATE TABLE IF NOT EXISTS restored_paths (
                path TEXT PRIMARY KEY COLLATE NOCASE, operation_id INTEGER NOT NULL
                REFERENCES file_operations(id))''')
            conn.execute('CREATE TABLE IF NOT EXISTS managed_directories(path TEXT PRIMARY KEY COLLATE NOCASE)')
            if version < 2:
                for row in conn.execute('SELECT source_path,destination_path FROM file_operations').fetchall():
                    self._remember_directory(conn, row['source_path'], row['destination_path'])
            conn.execute(f'PRAGMA user_version={SCHEMA_VERSION}')

    def begin_operation(self, filename, source_path, destination_path, category,
                        subcategory=None, fingerprint=None):
        now = datetime.now().astimezone()
        with self.connection() as conn:
            self._remember_directory(conn, source_path, destination_path)
            return conn.execute('''INSERT INTO file_operations
                (filename,source_path,destination_path,category,subcategory,timestamp,
                 operation_date,status,fingerprint) VALUES (?,?,?,?,?,?,?,'pending',?)''',
                (filename, str(source_path), str(destination_path), category, subcategory,
                 now.isoformat(timespec='seconds'), now.date().isoformat(), fingerprint)).lastrowid

    @staticmethod
    def _remember_directory(conn, source, destination):
        source, destination = Path(source), Path(destination)
        try:
            relative = destination.relative_to(source.parent)
            if source.is_absolute() and len(relative.parts) >= 2:
                conn.execute('INSERT OR IGNORE INTO managed_directories(path) VALUES (?)',
                             (str(source.parent / relative.parts[0]),))
        except ValueError:
            pass

    def is_managed_directory(self, path):
        with self.connection() as conn:
            return conn.execute('SELECT 1 FROM managed_directories WHERE path=?', (str(path),)).fetchone() is not None

    def dashboard_snapshot(self, limit=200):
        with self.connection() as conn:
            conn.execute('BEGIN')
            operations = [dict(row) for row in conn.execute('SELECT * FROM file_operations ORDER BY id DESC LIMIT ?', (limit,))]
            today = date.today().isoformat()
            total, daily = conn.execute("SELECT COUNT(*),COALESCE(SUM(operation_date=?),0) FROM file_operations WHERE status='completed'", (today,)).fetchone()
            categories = dict(conn.execute("SELECT category,COUNT(*) FROM file_operations WHERE status='completed' AND operation_date=? GROUP BY category ORDER BY COUNT(*) DESC,category", (today,)).fetchall())
            return operations, daily, total, categories

    def set_status(self, operation_id, status, error=None):
        if status not in {'pending', 'completed', 'failed', 'review', 'undo_pending', 'undone'}:
            raise ValueError('Unknown operation state.')
        with self.connection() as conn:
            conn.execute('UPDATE file_operations SET status=?,error=? WHERE id=?', (status, error, operation_id))

    def complete_undo(self, operation_id):
        with self.connection() as conn:
            row = conn.execute('SELECT source_path FROM file_operations WHERE id=?', (operation_id,)).fetchone()
            if not row:
                raise ValueError('Operation no longer exists.')
            conn.execute('UPDATE file_operations SET status=\'undone\',undone_at=?,error=NULL WHERE id=?',
                         (datetime.now().astimezone().isoformat(timespec='seconds'), operation_id))
            conn.execute('INSERT OR REPLACE INTO restored_paths(path,operation_id) VALUES (?,?)',
                         (row['source_path'], operation_id))

    def is_restored(self, path):
        with self.connection() as conn:
            return (conn.execute('SELECT 1 FROM restored_paths WHERE path=?', (str(path),)).fetchone() is not None
                    or conn.execute("SELECT 1 FROM file_operations WHERE source_path=? COLLATE NOCASE AND status IN ('review','pending','undo_pending')", (str(path),)).fetchone() is not None)

    def get_operation(self, operation_id):
        with self.connection() as conn:
            row = conn.execute('SELECT * FROM file_operations WHERE id=?', (operation_id,)).fetchone()
            return dict(row) if row else None

    def unfinished_operations(self):
        with self.connection() as conn:
            return [dict(row) for row in conn.execute("SELECT * FROM file_operations WHERE status IN ('pending','undo_pending') ORDER BY id")]

    def record_file_operation(self, filename, source_path, destination_path, category, subcategory=None):
        operation_id = self.begin_operation(filename, source_path, destination_path, category, subcategory)
        self.set_status(operation_id, 'completed')
        return operation_id

    def get_today_stats(self):
        with self.connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM file_operations WHERE status='completed' AND operation_date=?",
                                (date.today().isoformat(),)).fetchone()[0]

    def get_total_stats(self):
        with self.connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM file_operations WHERE status='completed'").fetchone()[0]

    def get_category_stats_today(self):
        with self.connection() as conn:
            return dict(conn.execute("SELECT category,COUNT(*) FROM file_operations WHERE status='completed' AND operation_date=? GROUP BY category ORDER BY COUNT(*) DESC,category",
                                     (date.today().isoformat(),)).fetchall())

    def get_weekly_stats(self):
        with self.connection() as conn:
            return [tuple(row) for row in conn.execute("SELECT operation_date,COUNT(*) FROM file_operations WHERE status='completed' AND operation_date>=? GROUP BY operation_date ORDER BY operation_date DESC",
                ((date.today() - timedelta(days=6)).isoformat(),))]

    def get_recent_operations(self, limit=100):
        with self.connection() as conn:
            return [dict(row) for row in conn.execute('SELECT * FROM file_operations ORDER BY id DESC LIMIT ?', (limit,))]


class _LazyDatabase:
    """No disk writes on import; CLI isolation is configured before first access."""
    def __init__(self):
        self._instance = None
        self._lock = threading.Lock()

    def __getattr__(self, name):
        with self._lock:
            if self._instance is None:
                self._instance = StatisticsDatabase()
        return getattr(self._instance, name)


statistics_db = _LazyDatabase()
