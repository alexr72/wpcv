Purpose of WPCV1 Orchestrator
The core purpose of the WPCV1 Orchestrator is to serve as an AI-powered assistant for software development. It's a workbench that deeply integrates powerful AI models into your coding workflow, moving beyond simple chat to allow the AI to act as a true collaborative partner.

It is designed to help developers with tasks like writing code, refactoring complex functions, and validating their work, all within a structured and safe environment that keeps a complete history of every change.

Key Capabilities: What Can It Do?
AI-Powered Code Generation and Modification: You can instruct AI agents to write new code or modify existing files directly within your project. The application provides the framework for the AI to safely edit your codebase.

Automated Code Revisioning: The system automatically tracks every change made by the AI. Before any file is modified, a "before" snapshot is saved, and an "after" snapshot is captured immediately after the change. This creates a complete, timestamped audit trail, ensuring no work is ever lost and all changes can be reviewed.

Multi-Agent Support: The system is not tied to a single AI provider. You can configure it to use different models from providers like OpenAI, DeepSeek, Google (Gemini), and others, allowing you to choose the best AI for the task at hand.

Interactive File System Navigation: Through its web interface, the tool provides a secure file browser. This allows you to easily point the AI to specific files or directories, giving it the necessary context for tasks that involve understanding your project's structure.

Code Validation: It includes a framework for validating your code against a predefined set of rules or "expectations," helping you maintain code quality and consistency.

Dual Interfaces: It offers both a full-featured web-based GUI for a rich, interactive experience and a simple, lightweight desktop application for quick tasks.
Core Features & How to Use Them
You can select one of three modes from the Mode dropdown.

1. Prompt Mode: Your AI Collaborator
This is the most powerful mode. Here you can chat with an AI agent to ask questions, write code, or modify existing files.

How to Use:

Select prompt from the Mode dropdown.
Choose your desired Agent (e.g., openai, deepseek).
(Optional but Recommended) Specify a Working Directory. Click the "Browse..." button to select the folder your task relates to. This gives the AI vital context, which is crucial for file modifications.
Click "Run". You will be prompted in the terminal window (where you started the server) to enter your message to the AI.
Asking the AI to Modify a File:

You can ask the AI to modify a file in plain English. For example: "Please refactor the function in src/utils/helpers.js to be more efficient."
When the AI modifies a file, the system automatically creates a "before" and "after" snapshot in the WPCV1/revisions folder, giving you a complete history of all changes.
2. Validate Mode: Check Your Work
Use this mode to validate a code file against a set of rules defined in an expectations.md file.

How to Use:
Select validate from the Mode dropdown.
Click "Browse..." next to File Path to select the code file you want to check.
(Optional) If you have a specific set of rules, you can select your custom expectations.md file. If you leave this blank, it will use the default rules.
Click "Run". The validation results will appear in the Output area.
3. Scaffold Mode: Create New Rules
This mode runs an interactive script to help you create a new expectations.md file.

How to Use:
Select scaffold from the Mode dropdown.
Click "Run".
Important: Look at the terminal window where you started the server. The script will ask you a series of questions there to help build the new expectations file.

