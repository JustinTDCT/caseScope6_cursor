#!/usr/bin/env python3
import sqlite3
import os

# Connect to the database
db_path = "/opt/casescope/casescope.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Add the new columns to the files table
    cursor.execute("ALTER TABLE files ADD COLUMN events_ingested INTEGER DEFAULT 0")
    print("Added events_ingested column")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("events_ingested column already exists")
    else:
        raise e

try:
    cursor.execute("ALTER TABLE files ADD COLUMN detections_found INTEGER DEFAULT 0")
    print("Added detections_found column")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("detections_found column already exists")
    else:
        raise e

# Commit the changes
conn.commit()
print("Migration completed successfully")

# Verify the columns exist
cursor.execute("PRAGMA table_info(files)")
columns = cursor.fetchall()
print("Current columns in files table:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
