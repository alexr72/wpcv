import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
AGENTS_FILE_PATH = os.path.join(CONFIG_DIR, 'agents.json')

# Predefined agent structures with placeholder API keys
AGENT_TEMPLATES = {
    "openai": {"api_key": "YOUR_OPENAI_API_KEY", "model": "gpt-4", "url": "https://api.openai.com/v1/chat/completions"},
    "deepseek": {"api_key": "YOUR_DEEPSEEK_API_KEY", "model": "deepseek-chat", "url": "https://api.deepseek.com/chat/completions"},
    "gemini": {"api_key": "YOUR_GEMINI_API_KEY", "model": "gemini-pro", "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"},
    "grok": {"api_key": "YOUR_GROK_API_KEY", "model": "grok-1", "url": "https://api.x.ai/v1/chat/completions"},
    "local": {"api_key": "NA", "model": "local-model", "url": "http://localhost:1234/v1/chat/completions"}
}

def create_default_config():
    """Creates or overwrites the agents.json file with default templates."""
    print("Creating default agent configuration file...")
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(AGENTS_FILE_PATH, 'w') as f:
            json.dump(AGENT_TEMPLATES, f, indent=2)
        print(f"✅ Default configuration successfully saved to {AGENTS_FILE_PATH}")
        print("Please edit this file to add your API keys.")
    except Exception as e:
        print(f"\n❌ Error creating default configuration: {e}")

if __name__ == "__main__":
    create_default_config()
