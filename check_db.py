import sqlite3
import os

db_path = 'db.sqlite3'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(store_orderitem);")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error: {e}")
    conn.close()
else:
    print("Database file not found.")
