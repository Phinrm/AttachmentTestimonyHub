import sqlite3
import os

class DBManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'testimonies.db')
        self._create_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        return conn

    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                age INTEGER,
                dob TEXT,
                course TEXT,
                year TEXT,
                email TEXT UNIQUE,
                university TEXT,
                username TEXT UNIQUE,
                password TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS testimonies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                full_name TEXT,
                company TEXT,
                company_email TEXT,
                university TEXT,
                start_date TEXT,
                end_date TEXT,
                department TEXT,
                rating INTEGER,
                notes TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()