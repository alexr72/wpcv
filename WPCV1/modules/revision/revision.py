"""
revision.py

Handles saving before/after versions of a file with timestamps.
"""

import os
from datetime import datetime

def save_revision(base_dir, file_path, content, label="before"):
    """
    Saves a version of a file to the revisions/ folder with a timestamp and label.

    :param base_dir: The base directory of the project.
    :param file_path: The relative path of the file being revisioned.
    :param content: The content of the file to save.
    :param label: The label for the revision (e.g., 'before', 'after').
    :return: The path to the saved revision file.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize the file_path to create a valid filename for the revision
    revision_filename = f"{label}_{timestamp}_{os.path.basename(file_path)}.txt"

    revisions_dir = os.path.join(base_dir, "revisions")
    os.makedirs(revisions_dir, exist_ok=True)

    revision_file_path = os.path.join(revisions_dir, revision_filename)

    with open(revision_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return revision_file_path
