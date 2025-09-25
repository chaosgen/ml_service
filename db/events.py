import sqlite3
import os

class EventDB:
    def __init__(self, db_path="events.db"):
        """ Initialize the database connection and create schema if needed. """
        self.db_path = db_path
        init_new = not os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        if init_new:
            self._create_schema()

    def _create_schema(self):
        """ Create the events table if it doesn't exist. """
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            user_id TEXT,
            timestamp INTEGER,
            score REAL
        )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_ts ON events(user_id, timestamp)")
        self.conn.commit()
        
    def insert(self, user_id, timestamp, score):
        """ Insert a new event into the database. """
        self.conn.execute(
            "INSERT INTO events (user_id, timestamp, score) VALUES (?, ?, ?)",
            (user_id, timestamp, score)
        )
        self.conn.commit()

    def get_recent_events(self, user_id=None, since_ts=None):
        """ Return events filtered by user_id and/or since timestamp. """
        query = "SELECT user_id, timestamp, score FROM events"
        params = []
        clauses = []

        if user_id is not None:
            clauses.append("user_id = ?")
            params.append(user_id)
        if since_ts is not None:
            clauses.append("timestamp >= ?")
            params.append(since_ts)
            
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY timestamp DESC"
        cur = self.conn.execute(query, params)
        return cur.fetchall()

    def count_users(self):
        """ Return count of unique users in the database. """
        cur = self.conn.execute("SELECT COUNT(DISTINCT user_id) FROM events")
        return cur.fetchone()[0]
    
    def get_user_history(self, user_id: str, since: int = None, until: int = None):
        """ Return full history of scores for a user, optionally filtered by time range. """
        query = "SELECT timestamp, score FROM events WHERE user_id = ?"
        params = [user_id]
        if since:
            query += " AND timestamp >= ?"
            params.append(since)
        if until:
            query += " AND timestamp <= ?"
            params.append(until)
        query += " ORDER BY timestamp ASC"
        rows = self.conn.execute(query, params).fetchall()

        return rows
    
    def close(self):
        self.conn.close()