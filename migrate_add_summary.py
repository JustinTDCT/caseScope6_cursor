#!/usr/bin/env python3
import sqlite3
import os

# Connect to the database
db_path = "/opt/casescope/casescope.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Create a summary table for faster dashboard queries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS case_summary (
            case_id INTEGER PRIMARY KEY,
            total_files INTEGER DEFAULT 0,
            total_events INTEGER DEFAULT 0,
            total_detections INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created case_summary table")
except sqlite3.OperationalError as e:
    print(f"Error creating case_summary table: {e}")

# Populate the summary table with current data
cursor.execute("""
    INSERT OR REPLACE INTO case_summary (case_id, total_files, total_events, total_detections)
    SELECT 
        case_id,
        COUNT(*) as total_files,
        COALESCE(SUM(events_ingested), 0) as total_events,
        COALESCE(SUM(detections_found), 0) as total_detections
    FROM files 
    WHERE status = 'completed'
    GROUP BY case_id
""")
print("Populated case_summary table")

# Commit the changes
conn.commit()
print("Migration completed successfully")

conn.close()
