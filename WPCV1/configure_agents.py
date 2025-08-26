import json
import os

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
AGENTS_FILE_PATH = os.path.join(CONFIG_DIR, 'agents.json')

# Predefined agent structures
AGENT_TEMPLATES = {
    "openai": {"api_key": "", "model": "gpt-4", "url": "https://api.openai.com/v1/chat/completions"},
    "deepseek": {"api_key": "", "model": "deepseek-chat", "url": "https://api.deepseek.com/chat/completions"},
    "gemini": {"api_key": "", "model": "gemini-pro", "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"},
    "grok": {"api_key": "", "model": "grok-1", "url": "https://api.x.ai/v1/chat/completions"},
    "local": {"api_key": "NA", "model": "local-model", "url": "http://localhost:1234/v1/chat/completions"}
}

def get_user_input(prompt, default=None):
    """Gets user input, providing a default value if available."""
    if default:
        return input(f"{prompt} [{default}]: ") or default
    return input(f"{prompt}: ")

def configure_agents():
    """Interactively configures the agents.json file."""
    print("--- WPCV1 Agent Configuration ---")

    agents_config = {}

    if os.path.exists(AGENTS_FILE_PATH):
        print(f"An existing configuration was found at {AGENTS_FILE_PATH}.")
        overwrite = input("Do you want to overwrite it? (y/N): ").lower()
        if overwrite != 'y':
            print("Configuration cancelled.")
            return

    while True:
        print("\nAvailable agent templates:", ", ".join(AGENT_TEMPLATES.keys()))
        agent_name = input("Enter the name of the agent to configure (or press Enter to finish): ").lower()

        if not agent_name:
            break

        if agent_name not in AGENT_TEMPLATES:
            print(f"Warning: '{agent_name}' is not a predefined template. You will need to enter all details manually.")
            template = {"api_key": "", "model": "", "url": ""}
        else:
            template = AGENT_TEMPLATES[agent_name]

        print(f"\n--- Configuring '{agent_name}' ---")
        api_key = get_user_input("Enter API Key", template.get("api_key"))
        model = get_user_input("Enter Model Name", template.get("model"))
        url = get_user_input("Enter API URL", template.get("url"))

        agents_config[agent_name] = {
            "api_key": api_key,
            "model": model,
            "url": url
        }

        print(f"Agent '{agent_name}' configured.")

    if not agents_config:
        print("\nNo agents configured. Exiting.")
        return

    # --- Save Configuration ---
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(AGENTS_FILE_PATH, 'w') as f:
            json.dump(agents_config, f, indent=2)
        print(f"\n✅ Configuration successfully saved to {AGENTS_FILE_PATH}")
    except Exception as e:
        print(f"\n❌ Error saving configuration: {e}")

if __name__ == "__main__":
    configure_agents()
