import sqlite3
import os

def check_db():
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- store_orderitem table info ---")
    try:
        cursor.execute("PRAGMA table_info(store_orderitem);")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error checking store_orderitem: {e}")
        
    print("\n--- last applied migrations for store ---")
    try:
        cursor.execute("SELECT name FROM django_migrations WHERE app='store' ORDER BY id DESC LIMIT 5;")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error checking migrations: {e}")
        
    conn.close()

if __name__ == "__main__":
    check_db()
