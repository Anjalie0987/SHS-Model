import sqlite3
import os

db_path = r"d:\CROP2\CROP2\shs-backend\shs_database.db"
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("SELECT stage, state, COUNT(*) FROM uploaded_csv_data GROUP BY stage, state;")
    rows = cursor.fetchall()
    if not rows:
        print("Table 'uploaded_csv_data' is empty.")
    else:
        print("Data in 'uploaded_csv_data':")
        for row in rows:
            print(f"Stage: {row[0]}, State: {row[1]}, Count: {row[2]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
