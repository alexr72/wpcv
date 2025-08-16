# WPCV1 Orchestrator

Modular validation and agent dispatch system for WordPress/Vue/JS stack.

## 🔧 Modes
- `prompt`: Send prompt to selected agent
- `validate`: Validate code file against expectations
- `scaffold`: Generate expectations.md and optionally validate
- `cmd-validate`: Check required CLI tools

## 🧠 Features
- Modular dispatcher and validator
- Centralized logging and context tracking
- GUI launcher with:
  - Mode and agent selection
  - File and expectations picker
  - Auto-validate toggle
  - Live preview of context and history
  - Persistent config via `gui_config.json`

## 📁 Structure
