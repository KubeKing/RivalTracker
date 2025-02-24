import sqlite3
import json
import logging
import os
from datetime import datetime

class Database:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config['database_path'])
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create matches table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS matches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        match_type TEXT,
                        friendly_team TEXT,
                        enemy_team TEXT,
                        raw_text TEXT,
                        image_path TEXT
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")

    def store_match(self, match_type, friendly_team, enemy_team, raw_text, image_path):
        """Store a new match record in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert team lists to JSON strings
                friendly_json = json.dumps(friendly_team)
                enemy_json = json.dumps(enemy_team)
                
                cursor.execute('''
                    INSERT INTO matches (match_type, friendly_team, enemy_team, raw_text, image_path)
                    VALUES (?, ?, ?, ?, ?)
                ''', (match_type, friendly_json, enemy_json, raw_text, image_path))
                
                conn.commit()
                self.logger.info("Match data stored successfully")
                return cursor.lastrowid
        except Exception as e:
            self.logger.error(f"Error storing match data: {str(e)}")
            return None

    def get_recent_matches(self, limit=10):
        """Retrieve recent matches from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, timestamp, match_type, friendly_team, enemy_team, image_path
                    FROM matches
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                matches = []
                for row in cursor.fetchall():
                    matches.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'match_type': row[2],
                        'friendly_team': json.loads(row[3]),
                        'enemy_team': json.loads(row[4]),
                        'image_path': row[5]
                    })
                
                return matches
        except Exception as e:
            self.logger.error(f"Error retrieving matches: {str(e)}")
            return []

    def export_matches(self, start_date=None, end_date=None):
        """Export matches within a date range as JSON."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, timestamp, match_type, friendly_team, enemy_team, raw_text, image_path
                    FROM matches
                    WHERE 1=1
                '''
                params = []
                
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date)
                
                query += " ORDER BY timestamp DESC"
                
                cursor.execute(query, params)
                
                matches = []
                for row in cursor.fetchall():
                    matches.append({
                        'id': row[0],
                        'timestamp': row[1],
                        'match_type': row[2],
                        'friendly_team': json.loads(row[3]),
                        'enemy_team': json.loads(row[4]),
                        'raw_text': row[5],
                        'image_path': row[6]
                    })
                
                return matches
        except Exception as e:
            self.logger.error(f"Error exporting matches: {str(e)}")
            return []

    def cleanup_old_records(self, days=30):
        """Clean up old records and their associated image files."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get old records
                cursor.execute('''
                    SELECT image_path FROM matches
                    WHERE datetime(timestamp) < datetime('now', '-? days')
                ''', (days,))
                
                # Delete associated image files
                for (image_path,) in cursor.fetchall():
                    if image_path and os.path.exists(image_path):
                        os.remove(image_path)
                
                # Delete old records
                cursor.execute('''
                    DELETE FROM matches
                    WHERE datetime(timestamp) < datetime('now', '-? days')
                ''', (days,))
                
                conn.commit()
                self.logger.info(f"Cleaned up records older than {days} days")
        except Exception as e:
            self.logger.error(f"Error cleaning up old records: {str(e)}")
