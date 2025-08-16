import shutil
import datetime

REQUIRED_CMDS = ["jq", "tree", "nano", "python3"]

def validate_commands():
    """
    Checks if required CLI commands are available.
    Returns a dict with status and suggestions.
    """
    timestamp = datetime.datetime.now().isoformat()
    results = {}

    for cmd in REQUIRED_CMDS:
        path = shutil.which(cmd)
        results[cmd] = {
            "found": bool(path),
            "path": path if path else "Not found",
            "suggest": f"sudo apt install {cmd}" if not path else None
        }

    return {
        "timestamp": timestamp,
        "validator": "cmd_validator",
        "results": results
    }
