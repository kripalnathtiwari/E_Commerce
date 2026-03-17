import sqlite3
import os

def fix_db():
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check current columns
    cursor.execute("PRAGMA table_info(store_orderitem);")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    if 'status' not in columns:
        print("Adding column 'status'...")
        try:
            # Using simple varchar. Django uses CharField
            cursor.execute("ALTER TABLE store_orderitem ADD COLUMN status varchar(20) NOT NULL DEFAULT 'Pending';")
            print("Status added.")
        except Exception as e:
            print(f"Failed to add status: {e}")
    else:
        print("Status column already exists.")
        
    if 'updated_at' not in columns:
        print("Adding column 'updated_at'...")
        try:
            cursor.execute("ALTER TABLE store_orderitem ADD COLUMN updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP;")
            print("updated_at added.")
        except Exception as e:
            print(f"Failed to add updated_at: {e}")
    else:
        print("updated_at column already exists.")

    conn.commit()
    conn.close()
    print("Database check/fix complete.")

if __name__ == "__main__":
    fix_db()
