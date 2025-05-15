import sqlite3

# Connect to database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

try:
    # Add "status" column if not exists
    cursor.execute('ALTER TABLE applicants ADD COLUMN status TEXT DEFAULT "Pending"')
    print("✅ 'status' column added successfully!")
except sqlite3.OperationalError as e:
    print("⚠️ Column may already exist or another issue:", e)

conn.commit()
conn.close()
