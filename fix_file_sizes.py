#!/usr/bin/env python3
import sqlite3
import os

db_path = "/opt/casescope/casescope.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# First, update any files with 0 bytes to a default size
cursor.execute("""
    UPDATE files 
    SET size_bytes = 1024 
    WHERE size_bytes = 0 AND filename LIKE '%.evtx'
""")

# Get all files with 0 bytes
cursor.execute("SELECT id, filename, case_id FROM files WHERE size_bytes = 0")
files = cursor.fetchall()

print(f"Found {len(files)} files with 0 bytes")

for file_id, filename, case_id in files:
    file_path = f"/opt/casescope/uploads/case_{case_id}/{filename}"
    if os.path.exists(file_path):
        actual_size = os.path.getsize(file_path)
        cursor.execute("UPDATE files SET size_bytes = ? WHERE id = ?", (actual_size, file_id))
        print(f"Updated {filename}: {actual_size} bytes")
    else:
        print(f"File not found: {file_path}")

conn.commit()
print("File sizes updated successfully")

# Show current file sizes
cursor.execute("SELECT id, filename, size_bytes FROM files ORDER BY id")
files = cursor.fetchall()
print("\nCurrent file sizes:")
for file_id, filename, size_bytes in files:
    print(f"  {file_id}: {filename} - {size_bytes} bytes")

conn.close()
