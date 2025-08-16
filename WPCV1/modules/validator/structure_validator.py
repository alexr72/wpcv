import os, json
from pathlib import Path

BASE = Path("/var/www/wordpress/scripts/WPCV1")
LOG = BASE / "logs/validator.log"

REQUIRED_PATHS = {
    "files": [
        BASE / "WPCV1.py",
        BASE / "validate_env.py",
        BASE / "config/agents.json",
        BASE / "config/user.json",
        BASE / "docs/expectations.md",
        BASE / "logs/session.log",
        BASE / "logs/validator.log",
        BASE / "modules/dispatcher.py",
        BASE / "modules/hrm.py",
        BASE / "modules/rewriter",
    ],
    "folders": [
        BASE / "archive",
        BASE / "config",
        BASE / "docs",
        BASE / "logs",
        BASE / "modules",
        BASE / "modules/dispatcher",
        BASE / "modules/expectations",
        BASE / "modules/revision",
        BASE / "modules/validator",
        BASE / "responses/code",
        BASE / "revisions",
    ]
}

def check_path(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "permissions": oct(path.stat().st_mode)[-3:] if path.exists() else None,
        "owner": path.owner() if path.exists() else None,
        "group": path.group() if path.exists() else None
    }

def validate_structure():
    results = {"folders": [], "files": []}
    for folder in REQUIRED_PATHS["folders"]:
        results["folders"].append(check_path(folder))
    for file in REQUIRED_PATHS["files"]:
        results["files"].append(check_path(file))

    with LOG.open("a") as log:
        log.write(f"\n--- Structure Validation ---\n")
        for category in results:
            for item in results[category]:
                status = "✓" if item["exists"] else "✗"
                log.write(f"{status} {item['path']} (perm: {item['permissions']}, owner: {item['owner']})\n")

    return results

if __name__ == "__main__":
    summary = validate_structure()
    print(json.dumps(summary, indent=2))
