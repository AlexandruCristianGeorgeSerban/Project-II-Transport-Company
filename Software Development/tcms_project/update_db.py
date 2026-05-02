import sqlite3
import os

# Calea trebuie sa fie identica cu cea din Controller
db_path = os.path.join(os.getcwd(), "instance", "database.sqlite")

def force_fix():
    print(f"🔍 Încerc să modific baza de date la: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ EROARE: Fișierul bazei de date NU a fost găsit la această cale!")
        print("💡 Sfat: Asigură-te că rulezi acest script din folderul principal al proiectului (unde este run.py).")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lista de coloane care lipsesc
        columns_to_add = [
            ("email", "TEXT DEFAULT ''"),
            ("profile_picture", "TEXT DEFAULT ''"),
            ("first_name", "TEXT DEFAULT ''"),
            ("last_name", "TEXT DEFAULT ''"),
            ("phone", "TEXT DEFAULT ''"),
            ("address", "TEXT DEFAULT ''")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"✅ Coloana '{col_name}' a fost adăugată cu succes.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"ℹ️ Coloana '{col_name}' există deja.")
                else:
                    print(f"⚠️ Eroare la coloana '{col_name}': {e}")
        
        conn.commit()
        conn.close()
        print("\n🚀 TOATE COLOANELE SUNT PREGĂTITE! Acum poți porni aplicația Flask.")
        
    except Exception as e:
        print(f"❌ Eroare generală: {e}")

if __name__ == "__main__":
    force_fix()