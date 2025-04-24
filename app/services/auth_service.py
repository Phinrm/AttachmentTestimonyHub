from ..utils.db_manager import DBManager
from ..utils.email_service import EmailService

class AuthService:
    def __init__(self):
        self.db = DBManager()
        self.email_service = EmailService()

    def signup(self, full_name, age, dob, course, year, email, university, username, password):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            return False
        cursor.execute("""
            INSERT INTO users (full_name, age, dob, course, year, email, university, username, password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (full_name, age, dob, course, year, email, university, username, password))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "signup", f"User {username} registered"))
        conn.commit()
        conn.close()
        return True

    def login(self, username, password):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone() is not None
        if result:
            cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                           (username, "login", f"User {username} logged in"))
            conn.commit()
        conn.close()
        return result

    def get_user_data(self, username):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        return {"id": row[0], "full_name": row[1], "email": row[6], "university": row[7]}

    def update_profile(self, username, email):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET email = ? WHERE username = ?", (email, username))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "update_profile", f"User {username} updated email to {email}"))
        conn.commit()
        conn.close()

    def delete_account(self, username):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM testimonies WHERE username = ?", (username,))
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "delete_account", f"User {username} deleted their account"))
        conn.commit()
        conn.close()

    def reset_password(self, email):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user:
            new_password = "temp123"
            cursor.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
            cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                           (user[0], "reset_password", f"User {user[0]} reset password for email {email}"))
            conn.commit()
            conn.close()
            self.email_service.send_reset_email(email, new_password)
            return True
        conn.close()
        return False

    def get_all_users(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, email, username FROM users")
        users = cursor.fetchall()
        conn.close()
        return users

    def admin_update_user(self, user_id, full_name, age, dob, course, year, email, university, username, password):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET full_name=?, age=?, dob=?, course=?, year=?, email=?, university=?, username=?, password=?
            WHERE id=?
        """, (full_name, age, dob, course, year, email, university, username, password, user_id))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "admin_update_user", f"Admin updated user {username}"))
        conn.commit()
        conn.close()

    def admin_delete_user(self, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id=?", (user_id,))
        username = cursor.fetchone()[0]
        cursor.execute("DELETE FROM testimonies WHERE username IN (SELECT username FROM users WHERE id=?)", (user_id,))
        cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
        cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                       (username, "admin_delete_user", f"Admin deleted user {username}"))
        conn.commit()
        conn.close()