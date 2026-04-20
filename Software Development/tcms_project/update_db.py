import sqlite3

try:
    with sqlite3.connect("instance/database.sqlite") as conn:
        cursor = conn.cursor()
        # Adaugam coloanele pentru coordonatele GPS
        cursor.execute("ALTER TABLE transport_requests ADD COLUMN current_lat REAL;")
        cursor.execute("ALTER TABLE transport_requests ADD COLUMN current_lng REAL;")
        conn.commit()
        print("Baza de date este pregatita pentru GPS.")
except Exception as e:
    print(f"Eroare (probabil coloanele exista deja): {e}")