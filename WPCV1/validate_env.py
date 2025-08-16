import os
import json
from datetime import datetime

BASE_PATH = "/var/www/wordpress/scripts/WPCV1"
LOG_PATH = os.path.join(BASE_PATH, "logs", "validator.log")

REQUIRED_FOLDERS = [
    "responses", "revisions", "config", "logs", "archive"
]

REQUIRED_FILES = [
    "config/user.json", "context.json", "conversation.txt"
]

__all__ = ["validate_environment"]

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}"
    with open(LOG_PATH, "a") as f:
        f.write(entry + "\n")

def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        log(f"📁 Created folder: {path}")
        return f"📁 Created folder: {path}"
    else:
        log(f"✅ Folder exists: {path}")
        return f"✅ Folder exists: {path}"

def check_file(path):
    if os.path.exists(path):
        log(f"✅ File exists: {path}")
        return f"✅ File exists: {path}"
    else:
        log(f"❌ Missing file: {path}")
        return f"❌ Missing file: {path}"

def validate_json(path, required_keys):
    try:
        with open(path, "r") as f:
            data = json.load(f)
        for key in required_keys:
            if key not in data:
                log(f"⚠️ '{key}' missing in {path}")
                return f"⚠️ '{key}' missing in {path}"
        log(f"✅ Valid JSON structure in {path}")
        return f"✅ Valid JSON structure in {path}"
    except Exception as e:
        log(f"❌ Error reading {path}: {e}")
        return f"❌ Error reading {path}: {e}"

def validate_environment(base_path=None):
    base_path = base_path or BASE_PATH
    results = []

    for folder in REQUIRED_FOLDERS:
        folder_path = os.path.join(base_path, folder)
        results.append(create_folder(folder_path))

    for file in REQUIRED_FILES:
        file_path = os.path.join(base_path, file)
        results.append(check_file(file_path))

    user_path = os.path.join(base_path, "config", "user.json")
    if os.path.exists(user_path):
        results.append(validate_json(user_path, ["username"]))

    return results
