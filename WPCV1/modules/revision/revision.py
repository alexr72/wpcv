"""
revision.py

Handles saving before/after versions with timestamps.
"""

import os
from datetime import datetime

def save_revision(code_str, label="before"):
    """
    Saves code to revisions/ folder with timestamp and label.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"revisions/{label}_{timestamp}.txt"
    os.makedirs("revisions", exist_ok=True)
    with open(filename, "w") as f:
        f.write(code_str)
    return filename
