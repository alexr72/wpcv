import os
import re

def load_expectations(path):
    """
    Parses expectations from a markdown file.
    Each bullet point becomes a rule string.
    """
    if not os.path.exists(path):
        print(f"❌ Expectations file not found: {path}")
        return []

    with open(path, "r") as f:
        content = f.read()

    # Match lines starting with - or * followed by space
    rules = re.findall(r"^[\-\*]\s+(.*)", content, re.MULTILINE)
    return [rule.strip() for rule in rules if rule.strip()]
