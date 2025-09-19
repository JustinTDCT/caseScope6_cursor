#!/usr/bin/env python3
import os
import re

def add_debug_to_file(file_path, pattern, debug_msg):
    """Add debug message after pattern in file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    if debug_msg not in content:
        content = re.sub(pattern, f'{pattern}\n    print(f"DEBUG: {debug_msg}")', content)
        
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Added debug to {file_path}")

# Enable debug in main files
files_to_debug = [
    ('app/files/service.py', 'def save_uploaded_file', 'save_uploaded_file called'),
    ('app/files/service.py', 'def process_file', 'process_file called'),
    ('app/files/service.py', 'def rerun_rules_for_file', 'rerun_rules_for_file called'),
    ('app/files/service.py', 'def reindex_file', 'reindex_file called'),
    ('app/files/routes.py', 'def upload_files', 'upload_files called'),
    ('app/files/routes.py', 'def rerun_rules', 'rerun_rules called'),
    ('app/files/routes.py', 'def reindex', 'reindex called'),
    ('app/cases/service.py', 'def get_case_stats', 'get_case_stats called'),
    ('app/cases/service.py', 'def get_system_stats', 'get_system_stats called'),
]

for file_path, pattern, debug_msg in files_to_debug:
    if os.path.exists(file_path):
        add_debug_to_file(file_path, pattern, debug_msg)
    else:
        print(f"File not found: {file_path}")

print("Debug messages enabled!")
