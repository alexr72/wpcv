# 🧠 WPCV1 Orchestrator

WPCV1 is a modular system for orchestrating development tasks with AI agents, primarily designed for a WordPress/Vue/JS stack but flexible enough for general coding. It features a robust backend, multiple user interfaces, and a powerful revisioning system.

## ✨ Features

- **AI Collaboration:** Interact with multiple AI agents (OpenAI, DeepSeek, Gemini, etc.) in a conversational manner.
- **File Modification & Revisioning:** Agents can modify files directly. The system automatically saves 'before' and 'after' revisions of every change.
- **Dynamic Environment:** No more hardcoded paths! The system is fully portable and works from any directory.
- **Multiple GUIs:**
    - **Web GUI:** A modern, browser-based interface with dynamic controls and a file browser. Recommended for most users.
    - **Tkinter GUI:** A simple, lightweight desktop application for quick tasks.
- **Configuration Helper:** An interactive script to easily configure your AI agent credentials.
- **Validation & Scaffolding:** Tools to validate your code and scaffold new files.

---

## 🚀 Getting Started

### 1. Configuration

Before you can use the AI features, you need to configure your agent credentials. Run the interactive configuration script:

```bash
python3 WPCV1/configure_agents.py
```

This will guide you through creating the `WPCV1/config/agents.json` file.

### 2. Running the Web GUI (Recommended)

The web GUI provides the best user experience. It requires a PHP-enabled web server.

1.  **Start a PHP web server.** A simple way to do this is to use the built-in PHP server. Navigate to the project's root directory and run:
    ```bash
    php -S localhost:8000
    ```
2.  **Open your browser.** Navigate to `http://localhost:8000/WPCV1_GUI/`.

You can now use the web interface to interact with the system.

### 3. Running the Tkinter Desktop GUI

For a quick, simple interface without needing a web server, you can use the Tkinter GUI.

```bash
python3 WPCV1/gui_launcher.py
```

---

## 🤖 AI Agent Usage

### Standard Prompts

In `prompt` mode, you can have a conversation with the AI agent. You can also specify a **Working Directory** to give the agent context for your request.

### File Modifications

The agent can modify files for you. To do this, simply ask the agent to modify a file in your prompt (e.g., "refactor the following code in `path/to/my/file.js`"). The agent will be instructed to format its response in a special way that the system can parse.

When the agent modifies a file:
1.  A `before` snapshot of the file is saved to the `WPCV1/revisions/` directory.
2.  The file is overwritten with the new content from the agent.
3.  An `after` snapshot is also saved to the `revisions` directory.

This provides a complete history of all changes made by the AI.
