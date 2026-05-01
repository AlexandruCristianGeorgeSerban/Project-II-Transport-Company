import os
import sqlite3
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

DB_PATH = "instance/database.sqlite"

class ProfileController:
    def get_user_profile(self, user_id: int) -> dict:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    def update_profile(self, user_id: int, new_username: str, email: str, first_name: str, last_name: str, phone: str, address: str, profile_pic=None) -> dict:
        try:
            pic_filename = None
            
            if profile_pic and profile_pic.filename != '':
                safe_name = secure_filename(profile_pic.filename)
                pic_filename = f"user_{user_id}_{safe_name}"
                
                upload_path = os.path.join(os.getcwd(), 'app', 'static', 'img', 'avatars')
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path, exist_ok=True)
                
                profile_pic.save(os.path.join(upload_path, pic_filename))

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Verifica duplicat username
                cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, user_id))
                if cursor.fetchone():
                    return {"success": False, "message": "Username already taken."}

                if pic_filename:
                    cursor.execute("""
                        UPDATE users 
                        SET username=?, email=?, first_name=?, last_name=?, phone=?, address=?, profile_picture=? 
                        WHERE id=?
                    """, (new_username, email, first_name, last_name, phone, address, pic_filename, user_id))
                else:
                    cursor.execute("""
                        UPDATE users 
                        SET username=?, email=?, first_name=?, last_name=?, phone=?, address=? 
                        WHERE id=?
                    """, (new_username, email, first_name, last_name, phone, address, user_id))
                
                conn.commit()
                return {"success": True, "message": "Profile updated!", "new_username": new_username, "new_pic": pic_filename}
        
        except Exception as e:
            print(f"\n❌ EROARE CRITICĂ LA UPDATE: {e}\n")
            return {"success": False, "message": "Failed to update profile."}

    def change_password(self, user_id: int, current_pw: str, new_pw: str) -> dict:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if not row or not check_password_hash(row[0], current_pw):
                    return {"success": False, "message": "Incorrect password."}
                
                new_hash = generate_password_hash(new_pw)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                conn.commit()
                return {"success": True, "message": "Password changed!"}
        except Exception as e:
            print(f"❌ PWD Error: {e}")
            return {"success": False, "message": "Error changing password."}

    def delete_account(self, user_id: int) -> dict:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                return {"success": True, "message": "Account deleted."}
        except Exception as e:
            print(f"❌ Delete Error: {e}")
            return {"success": False, "message": "Error deleting account."}