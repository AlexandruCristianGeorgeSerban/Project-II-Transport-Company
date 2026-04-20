import sqlite3

try:
    with sqlite3.connect("instance/database.sqlite") as conn:
        cursor = conn.cursor()
        
        # Adaugam coloana lipsa de pret in tabel
        cursor.execute("ALTER TABLE transport_requests ADD COLUMN estimated_price REAL;")
        
        conn.commit()
        print("🎉 SUCCES TOTAL! Coloana 'estimated_price' a fost adaugata!")
except Exception as e:
    print(f"Eroare (probabil exista deja): {e}")