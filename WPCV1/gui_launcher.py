import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import json

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
AGENTS_FILE = os.path.join(BASE_DIR, 'config', 'agents.json')

def load_agents():
    """Loads agent names from the configuration file."""
    if not os.path.exists(AGENTS_FILE):
        messagebox.showerror("Config Error", f"Agent configuration file not found at:\n{AGENTS_FILE}\n\nPlease run configure_agents.py first.")
        return []
    try:
        with open(AGENTS_FILE, 'r') as f:
            agents_config = json.load(f)
        return list(agents_config.keys())
    except Exception as e:
        messagebox.showerror("Config Error", f"Error reading agents.json: {e}")
        return []

AGENTS = load_agents()
MODES = {
    "prompt": "Send a prompt to selected agent and log response",
    "validate": "Run validation pipeline on selected code file",
    "scaffold": "Generate expectations.md scaffold and optionally validate",
    "cmd-validate": "Check required CLI commands and paths"
}

def run_script(mode, agent=None, file_path=None, expect_path=None, directory=None):
    cmd = ["python3", os.path.join(BASE_DIR, "WPCV1.py"), "--mode", mode]

    if mode == "prompt" and agent:
        cmd += ["--agent", agent]
        if directory:
            cmd += ["--directory", directory]
    if mode == "validate" and file_path:
        cmd += ["--file", file_path]
        if expect_path:
            cmd += ["--expect", expect_path]
    if mode == "cmd-validate":
        cmd += ["--validate-only"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, result.stdout)
    except Exception as e:
        messagebox.showerror("Execution Error", str(e))

def browse_file(entry_widget):
    path = filedialog.askopenfilename()
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, path)

def launch_gui():
    root = tk.Tk()
    root.title("WPCV1 GUI Orchestrator")
    root.geometry("800x600")

    # === Mode Selection ===
    tk.Label(root, text="Select Mode:", font=("Arial", 12)).pack(pady=5)
    mode_var = tk.StringVar(value="prompt")
    mode_menu = ttk.Combobox(root, textvariable=mode_var, values=list(MODES.keys()), state="readonly")
    mode_menu.pack()

    mode_desc = tk.Label(root, text=MODES["prompt"], wraplength=600, fg="gray")
    mode_desc.pack(pady=2)

    def update_mode_desc(event):
        selected = mode_var.get()
        mode_desc.config(text=MODES[selected])
    mode_menu.bind("<<ComboboxSelected>>", update_mode_desc)

    # === Agent Selection ===
    tk.Label(root, text="Select Agent:", font=("Arial", 12)).pack(pady=5)
    agent_var = tk.StringVar(value="local")
    agent_menu = ttk.Combobox(root, textvariable=agent_var, values=AGENTS, state="readonly")
    agent_menu.pack()

    # === File Path ===
    tk.Label(root, text="Code File (for validation):").pack(pady=5)
    file_entry = tk.Entry(root, width=80)
    file_entry.pack()
    tk.Button(root, text="Browse", command=lambda: browse_file(file_entry)).pack()

    # === Expectations Path ===
    tk.Label(root, text="Expectations File (optional):").pack(pady=5)
    expect_entry = tk.Entry(root, width=80)
    expect_entry.pack()
    tk.Button(root, text="Browse", command=lambda: browse_file(expect_entry)).pack()

    # === Directory Path ===
    tk.Label(root, text="Working Directory (for prompt mode):").pack(pady=5)
    dir_entry = tk.Entry(root, width=80)
    dir_entry.pack()
    tk.Button(root, text="Browse", command=lambda: browse_file(dir_entry)).pack()

    # === Run Button ===
    tk.Button(root, text="Run", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
              command=lambda: run_script(mode_var.get(), agent_var.get(), file_entry.get(), expect_entry.get(), dir_entry.get())
    ).pack(pady=10)

    # === Output Display ===
    tk.Label(root, text="Output:", font=("Arial", 12)).pack(pady=5)
    output_text = tk.Text(root, wrap="word", height=20)
    output_text.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    launch_gui()
