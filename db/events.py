import sqlite3
import os

class EventDB:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        init_new = not os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        if init_new:
            self._create_schema()

    def _create_schema(self):
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
        self.conn.execute(
            "INSERT INTO events (user_id, timestamp, score) VALUES (?, ?, ?)",
            (user_id, timestamp, score)
        )
        self.conn.commit()

    def get_recent_events(self, user_id=None, since_ts=None):
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
        cur = self.conn.execute("SELECT COUNT(DISTINCT user_id) FROM events")
        return cur.fetchone()[0]