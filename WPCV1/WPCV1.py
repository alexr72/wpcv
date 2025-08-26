#!/usr/bin/env python3

import os, json, datetime, requests, logging, argparse, re
from modules.dispatcher import dispatcher as validation_dispatcher
from modules.validator import cmd_validator
from modules.logger.logger import log_conversation
from modules.expectations.scaffold import scaffold_expectations
from modules.revision.revision import save_revision

# === Setup Paths ===
base_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(base_dir, 'config', 'user.json')
response_dir = os.path.join(base_dir, 'responses')
context_file = os.path.join(base_dir, 'context.json')
history_file = os.path.join(base_dir, 'conversation.txt')
expectations_default = os.path.join(base_dir, "docs", "expectations.md")
log_file = os.path.join(base_dir, 'logs', 'session.log')

os.makedirs(response_dir, exist_ok=True)
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(filename=log_file, level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s')

# === Utility Functions ===
def load_user_config():
    try:
        with open(config_file) as f:
            user_config = json.load(f)
            return user_config.get('username', 'UnknownUser'), user_config.get('revision', 'Unversioned')
    except Exception as e:
        logging.warning(f"User config load failed: {e}")
        return 'UnknownUser', 'Unversioned'

def load_expectations(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        logging.warning("Expectations.md not found.")
        return ""

def save_response(prompt, reply, revision_tag, timestamp):
    response_file = os.path.join(response_dir, f'{timestamp}.txt')
    with open(response_file, 'w') as f:
        f.write(f'User: {prompt}\nAI: {reply}\nRevision: {revision_tag}\n')
    logging.info(f"Response saved to {response_file}")
    return response_file

def append_history(prompt, reply, revision_tag, timestamp):
    with open(history_file, 'a') as f:
        f.write(f'{timestamp}\nUser: {prompt}\nAI: {reply}\nRevision: {revision_tag}\n\n')
    logging.info("Conversation history updated.")

def update_context(prompt, reply, timestamp, username, revision_tag):
    context = {
        "last_prompt": prompt,
        "last_response": reply,
        "last_timestamp": timestamp,
        "user": username,
        "revision": revision_tag
    }
    with open(context_file, 'w') as f:
        json.dump(context, f, indent=2)
    logging.info("Context.json updated.")

def save_script_revision(timestamp):
    script_path = os.path.realpath(__file__)
    revision_copy = os.path.join(response_dir, f'{timestamp}_WPCV1.py')
    try:
        with open(script_path, 'r') as src, open(revision_copy, 'w') as dst:
            dst.write(src.read())
        logging.info(f"Script revision saved to {revision_copy}")
    except Exception as e:
        logging.warning(f"Script revision save failed: {e}")

def call_agent(agent_name, prompt, working_dir=None):
    if working_dir:
        prompt = f"You are working in the directory: {working_dir}\n\n{prompt}"

    system_prompt = """
To modify a file, please format your response within a special block like this:
<file_modification>
<file_path>/path/to/your/file.ext</file_path>
<content>
... your new file content here ...
</content>
</file_modification>
"""
    prompt = system_prompt + prompt

    agents_file = os.path.join(base_dir, 'config', 'agents.json')
    try:
        with open(agents_file) as f:
            agents = json.load(f)
        agent = agents.get(agent_name)
        if not agent:
            return f"⚠️ Agent '{agent_name}' not found in config."

        headers = {
            'Authorization': f'Bearer {agent["api_key"]}',
            'Content-Type': 'application/json'
        }

        if agent_name == "gemini":
            data = { "contents": [{ "parts": [{ "text": prompt }] }] }
        else:
            data = { "model": agent["model"], "messages": [{ "role": "user", "content": prompt }] }

        response = requests.post(agent["url"], headers=headers, json=data).json()

        if agent_name == "gemini":
            return response["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return response["choices"][0]["message"]["content"]

    except Exception as e:
        logging.error(f"{agent_name} API call failed: {e}")
        return f"⚠️ API call failed: {e}"

def run_validation_pipeline(code_path, expectations_path):
    try:
        with open(code_path, 'r') as f:
            code_str = f.read()

        results = validation_dispatcher.run_validation(code_str, expectations_path)

        print("\n🔍 Validation Results:")
        for key, value in results.items():
            print(f"\n{key.upper()}:\n{value if value else '✅ No issues found.'}")

        logging.info("Validation pipeline completed.")
    except Exception as e:
        logging.error(f"Validation pipeline failed: {e}")
        print(f"❌ Validation error: {e}")

# === Main Entry Point ===
def main():
    parser = argparse.ArgumentParser(description="WPCV1 Orchestrator")
    parser.add_argument("--mode", choices=["prompt", "validate", "scaffold"], help="Choose execution mode")
    parser.add_argument("--file", type=str, help="Path to code file for validation")
    parser.add_argument("--expect", type=str, help="Path to expectations file")
    parser.add_argument("--agent", choices=["deepseek", "openai", "grok", "gemini", "local"], help="Specify agent to route prompt to")
    parser.add_argument("--directory", type=str, help="Path to the working directory for the agent")
    parser.add_argument("--validate-only", action="store_true", help="Run CMD validator only and exit")
    args = parser.parse_args()

    username, revision_tag = load_user_config()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    if args.validate_only:
        cmd_result = cmd_validator.validate_commands()
        log_conversation({
            "timestamp": cmd_result["timestamp"],
            "agent": "cmd_validator",
            "prompt": "Validate required CLI commands",
            "response": cmd_result["results"]
        })

        print("🔍 CMD Validation Results:")
        for cmd, info in cmd_result["results"].items():
            status = "✅" if info["found"] else "❌"
            print(f"{status} {cmd}: {info['path']}")
            if info["suggest"]:
                print(f"   ↪ Suggest: {info['suggest']}")
        return

    if args.mode == "scaffold":
        result = scaffold_expectations(base_dir)
        if result:
            path, folder, agent, expectation_type, auto_validate = result
            print(f"\n✅ Expectations saved to: {path}")
            if auto_validate:
                expectations_path = os.path.join(base_dir, "docs", f"{expectation_type}.md")
                code_path = os.path.join(base_dir, folder, "main.js")  # or dynamically scan folder
                run_validation_pipeline(code_path, expectations_path)
        return

    if args.mode == 'validate' and args.file:
        expectations_path = args.expect if args.expect else expectations_default
        run_validation_pipeline(args.file, expectations_path)

    elif args.mode == 'prompt' and args.agent:
        prompt_text = input(f'{username}, enter your prompt: ')
        reply = call_agent(args.agent, prompt_text, args.directory)

        # Check for file modification block
        mod_match = re.search(r'<file_modification>(.*?)</file_modification>', reply, re.DOTALL)
        if mod_match:
            mod_block = mod_match.group(1)
            path_match = re.search(r'<file_path>(.*?)</file_path>', mod_block, re.DOTALL)
            content_match = re.search(r'<content>(.*?)</content>', mod_block, re.DOTALL)

            if path_match and content_match:
                file_path_relative = path_match.group(1).strip()
                file_path_absolute = os.path.join(base_dir, file_path_relative)
                new_content = content_match.group(1).strip()

                print(f"\n✨ Agent has requested to modify the file: {file_path_relative}")
                try:
                    # Read original content
                    original_content = ""
                    if os.path.exists(file_path_absolute):
                        with open(file_path_absolute, 'r', encoding='utf-8') as f:
                            original_content = f.read()

                    # Save 'before' revision
                    save_revision(base_dir, file_path_relative, original_content, 'before')

                    # Write new content
                    with open(file_path_absolute, 'w', encoding='utf-8') as f:
                        f.write(new_content)

                    # Save 'after' revision
                    save_revision(base_dir, file_path_relative, new_content, 'after')

                    print(f"✅ Successfully modified file and saved revisions.")
                    # Remove the modification block from the reply shown to the user
                    reply = re.sub(r'<file_modification>.*?</file_modification>', '', reply, flags=re.DOTALL).strip()

                except Exception as e:
                    print(f"❌ Error modifying file: {e}")

        print(f"\n🧠 AI Reply:\n{'-'*40}\n{reply}\n{'-'*40}")
        print("\n🤔 Would you like to challenge that?")
        save_response(prompt_text, reply, revision_tag, timestamp)
        append_history(prompt_text, reply, revision_tag, timestamp)
        update_context(prompt_text, reply, timestamp, username, revision_tag)
        save_script_revision(timestamp)

    else:
        print("⚠️ No valid mode selected. Use --mode prompt --agent deepseek or --mode validate --file path/to/code.js")

if __name__ == "__main__":
    main()
