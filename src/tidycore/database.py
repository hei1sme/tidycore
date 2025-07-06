# tidycore/database.py
import sqlite3
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from .utils import get_absolute_path

class StatisticsDatabase:
    """Manages the SQLite database for tracking file organization statistics."""
    
    def __init__(self):
        self.db_path = get_absolute_path("tidycore_stats.db")
        self.logger = logging.getLogger("TidyCore")
        self._init_database()
    
    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table for daily statistics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_stats (
                        date TEXT PRIMARY KEY,
                        files_organized INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table for detailed file operations
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_operations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        destination_path TEXT NOT NULL,
                        category TEXT NOT NULL,
                        subcategory TEXT,
                        operation_type TEXT DEFAULT 'organize',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Table for category statistics
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS category_stats (
                        date TEXT,
                        category TEXT,
                        count INTEGER DEFAULT 0,
                        PRIMARY KEY (date, category)
                    )
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
    
    def record_file_operation(self, filename: str, source_path: str, 
                            destination_path: str, category: str, 
                            subcategory: Optional[str] = None):
        """Record a file organization operation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert file operation
                cursor.execute("""
                    INSERT INTO file_operations 
                    (filename, source_path, destination_path, category, subcategory)
                    VALUES (?, ?, ?, ?, ?)
                """, (filename, source_path, destination_path, category, subcategory))
                
                # Update daily stats
                today = date.today().isoformat()
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_stats (date, files_organized)
                    VALUES (?, COALESCE((SELECT files_organized FROM daily_stats WHERE date = ?), 0) + 1)
                """, (today, today))
                
                # Update category stats
                cursor.execute("""
                    INSERT OR REPLACE INTO category_stats (date, category, count)
                    VALUES (?, ?, COALESCE((SELECT count FROM category_stats WHERE date = ? AND category = ?), 0) + 1)
                """, (today, category, today, category))
                
                conn.commit()
                
        except sqlite3.Error as e:
            self.logger.error(f"Database record error: {e}")
    
    def get_today_stats(self) -> int:
        """Get the number of files organized today."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                today = date.today().isoformat()
                
                cursor.execute("SELECT files_organized FROM daily_stats WHERE date = ?", (today,))
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except sqlite3.Error as e:
            self.logger.error(f"Database query error: {e}")
            return 0
    
    def get_total_stats(self) -> int:
        """Get the total number of files organized."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT SUM(files_organized) FROM daily_stats")
                result = cursor.fetchone()
                return result[0] if result and result[0] else 0
                
        except sqlite3.Error as e:
            self.logger.error(f"Database query error: {e}")
            return 0
    
    def get_category_stats_today(self) -> Dict[str, int]:
        """Get today's category breakdown."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                today = date.today().isoformat()
                
                cursor.execute("""
                    SELECT category, count FROM category_stats 
                    WHERE date = ? ORDER BY count DESC
                """, (today,))
                
                return dict(cursor.fetchall())
                
        except sqlite3.Error as e:
            self.logger.error(f"Database query error: {e}")
            return {}
    
    def get_weekly_stats(self) -> List[Tuple[str, int]]:
        """Get the last 7 days of statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT date, files_organized FROM daily_stats 
                    WHERE date >= date('now', '-7 days')
                    ORDER BY date DESC
                """)
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            self.logger.error(f"Database query error: {e}")
            return []
    
    def get_recent_operations(self, limit: int = 10) -> List[Dict]:
        """Get recent file operations."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT filename, category, subcategory, timestamp
                    FROM file_operations 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                operations = []
                for row in cursor.fetchall():
                    operations.append({
                        'filename': row[0],
                        'category': row[1],
                        'subcategory': row[2],
                        'timestamp': row[3]
                    })
                
                return operations
                
        except sqlite3.Error as e:
            self.logger.error(f"Database query error: {e}")
            return []

# Create a global instance
statistics_db = StatisticsDatabase()
