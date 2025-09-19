#!/usr/bin/env python3
import sqlite3
import os
import glob

def fix_filenames():
    db_path = "/opt/casescope/casescope.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all files with error status
    cursor.execute("SELECT id, filename, case_id, status FROM files WHERE status = 'error'")
    files = cursor.fetchall()
    
    print(f"Found {len(files)} files with error status")
    
    for file_id, filename, case_id, status in files:
        print(f"\nProcessing file {file_id}: {filename}")
        
        # Look for the actual file in uploads directory
        upload_dir = f"/opt/casescope/uploads/case_{case_id}"
        if os.path.exists(upload_dir):
            # Find files that match the pattern (number_prefix + original_name)
            pattern = f"{upload_dir}/*{filename}"
            matching_files = glob.glob(pattern)
            
            if matching_files:
                actual_file = matching_files[0]
                actual_filename = os.path.basename(actual_file)
                print(f"  Found actual file: {actual_filename}")
                
                # Update the database with the correct filename
                cursor.execute("UPDATE files SET filename = ?, status = 'queued', error_message = NULL WHERE id = ?", 
                             (actual_filename, file_id))
                
                # Re-process the file
                print(f"  Re-processing file {file_id}")
                cursor.execute("UPDATE files SET status = 'processing', progress = 0 WHERE id = ?", (file_id,))
                
            else:
                print(f"  No matching file found for {filename}")
        else:
            print(f"  Upload directory not found: {upload_dir}")
    
    conn.commit()
    print("\nFilename fix completed!")
    
    # Show updated files
    cursor.execute("SELECT id, filename, status FROM files ORDER BY id")
    files = cursor.fetchall()
    print("\nUpdated files:")
    for file_id, filename, status in files:
        print(f"  {file_id}: {filename} - {status}")
    
    conn.close()

if __name__ == "__main__":
    fix_filenames()
