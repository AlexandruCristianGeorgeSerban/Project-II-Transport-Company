import sqlite3

# Conectarea la baza de date
db_path = "instance/database.sqlite"

try:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Facem update la coloana 'role' pentru user
        cursor.execute("UPDATE users SET role = 'Staff' WHERE id = 3")
        conn.commit()
        
        if cursor.rowcount > 0:
            print("Succes! Userul a fost actualizat. 🎉")
        else:
            print("Nu s-a găsit niciun user cu acel ID. Verifică ID-ul!")
            
except sqlite3.Error as e:
    print(f"Eroare la baza de date: {e}")