import os
import json
from datetime import datetime

BASE_PATH = "/var/www/wordpress/scripts/WPCV1"

def log_conversation(entry: dict):
    timestamp = entry.get("timestamp", datetime.now().isoformat())
    revision = get_revision()
    agent = entry.get("agent", "unknown")
    prompt = entry.get("prompt", "")
    response = entry.get("response", "")

    convo_path = os.path.join(BASE_PATH, "conversation.txt")
    with open(convo_path, "a") as f:
        f.write(f"[{timestamp}] ({revision}) {agent} > {prompt}\n")
        f.write(f"[{timestamp}] ({revision}) {agent} < {response}\n\n")

    response_dir = os.path.join(BASE_PATH, "responses", "code")
    os.makedirs(response_dir, exist_ok=True)
    response_file = os.path.join(response_dir, f"{timestamp}.txt")
    with open(response_file, "w") as f:
        json.dump(entry, f, indent=2)

def get_revision():
    try:
        with open(os.path.join(BASE_PATH, "config", "user.json")) as f:
            user = json.load(f)
            return user.get("revision", "unknown")
    except Exception:
        return "unknown"
