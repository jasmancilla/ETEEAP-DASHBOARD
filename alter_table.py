import sqlite3

# Connect to your database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Alter the table to add course column
try:
    cursor.execute('ALTER TABLE applicants ADD COLUMN course TEXT')
    print("Column 'course' added successfully.")
except Exception as e:
    print("Error:", e)

conn.commit()
conn.close()
