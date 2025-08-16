"""
expectations.py

Loads and parses expectations.md files.
"""

def load_expectations(path):
    """
    Loads expectations from a markdown file.
    Returns a list of expectation strings.
    """
    with open(path, "r") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]
