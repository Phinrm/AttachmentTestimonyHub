from ..utils.db_manager import DBManager

class TestimonyService:
    def __init__(self):
        self.db = DBManager()

    def submit_testimony(self, username, full_name, company, company_email, university, start_date, end_date, department, rating, notes):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO testimonies (username, full_name, company, company_email, university, start_date, end_date, department, rating, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, full_name, company, company_email, university, start_date, end_date, department, rating, notes))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "submit_testimony", f"User {username} submitted a testimony for {company}"))
        conn.commit()
        conn.close()

    def get_all_testimonies(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM testimonies")
        testimonies = cursor.fetchall()
        conn.close()
        return testimonies

    def search_testimonies(self, query):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        query = f"%{query}%"
        cursor.execute("""
            SELECT * FROM testimonies
            WHERE full_name LIKE ? OR company LIKE ? OR university LIKE ? OR notes LIKE ?
        """, (query, query, query, query))
        testimonies = cursor.fetchall()
        conn.close()
        return testimonies

    def admin_update_testimony(self, testimony_id, username, full_name, company, company_email, university, start_date, end_date, department, rating, notes):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE testimonies SET username=?, full_name=?, company=?, company_email=?, university=?, start_date=?, end_date=?, department=?, rating=?, notes=?
            WHERE id=?
        """, (username, full_name, company, company_email, university, start_date, end_date, department, rating, notes, testimony_id))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "admin_update_testimony", f"Admin updated testimony ID {testimony_id}"))
        conn.commit()
        conn.close()

    def admin_delete_testimony(self, testimony_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM testimonies WHERE id=?", (testimony_id,))
        username = cursor.fetchone()[0]
        cursor.execute("DELETE FROM testimonies WHERE id=?", (testimony_id,))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "admin_delete_testimony", f"Admin deleted testimony ID {testimony_id}"))
        conn.commit()
        conn.close()

    def get_all_logs(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, action, details, timestamp FROM logs")
        logs = cursor.fetchall()
        conn.close()
        return logs