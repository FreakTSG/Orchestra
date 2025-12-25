# 🎻 Orchestra - Multi-Agent AI Coding Environment

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Your AI coding team at your fingertips**

Orchestra is a powerful multi-agent coding environment that orchestrates multiple AI coding assistants (Claude, Gemini, OpenAI) to work together on your coding tasks. It runs them in parallel, evaluates their solutions, and lets you choose the best one with full diff previews and automatic backups.

## ✨ Features

- **🚀 Parallel Execution** - Run multiple AI agents simultaneously for faster results
- **📊 Peer Evaluation** - Agents evaluate each other's solutions to rank by quality
- **📂 Context Awareness** - Automatically scans your codebase for better, contextual solutions
- **🔍 File Operations Detection** - Automatically detects create/modify/delete operations
- **📋 Interactive Selection** - Preview diffs before applying changes
- **💾 Automatic Backups** - Safe changes with built-in backup and rollback system
- **🎻 REPL Mode** - Persistent interactive environment for continuous work

## 📦 Installation

### Quick Install (Windows)

Run the installation script:

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

Or install manually:

```powershell
# Clone or download the repository
git clone https://github.com/your-username/orchestra.git
cd orchestra

# Install in editable mode
pip install -e .
```

### Manual Install (All Platforms)

```bash
# Install Orchestra
pip install orchestra-ma

# Or from source
pip install -e .
```

### Requirements

- Python 3.8 or higher
- pip (comes with Python)

## 🤖 AI CLI Tools (Optional but Recommended)

Orchestra works best with AI CLI tools installed. These are **NOT required** - Orchestra will work with whatever tools you have installed.

### Install AI CLI Tools

**Claude CLI:**
```powershell
# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex
```

**Gemini CLI:**
```bash
npm install -g @google/gemini-cli
```

**OpenAI Codex:**
```bash
npm install -g @openai/codex
```

> **Note:** Orchestra automatically detects which CLI tools you have installed and uses them. No API keys required!

## 🚀 Quick Start

### Start Orchestra

```powershell
orchestra
```

Or:

```bash
python -m orchestra
```

### Basic Usage

```
orchestra> Add error handling to all functions

🎼 Mode: IMPLEMENT
📝 Query: Add error handling to all functions

🚀 Dispatching to 3 agent(s)...

📊 Ranked Solutions
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Rank ┃ Agent             ┃ Score  ┃ Files  ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│ 🥇 #1 │ Claude CLI        │ 85/100 │ 3 files│
│ 🥈 #2 │ Gemini CLI        │ 72/100 │ 2 files│
│ 🥉 #3 │ OpenAI CLI        │ 65/100 │ 2 files│
└──────┴───────────────────┴────────┴────────┘

[Preview and apply changes...]
```

## 📖 Commands

### Coding Queries

```
# Ask agents to implement/fix/refactor
Add error handling to auth.py
Refactor the database layer
Fix the bug in user service

# Get code review only
Review utils.py !review

# Get explanations only
Explain how this works !explain
```

### Directory Management

```
pwd                    # Show current directory
cd ./backend          # Change directory
context               # Show codebase context
```

### Agent Management

```
agents                # List available AI agents
set agents claude,gemini    # Choose specific agents
```

### Configuration

```
set limit 20          # Set context file limit
set nocontext         # Disable context
set context           # Enable context
```

### Backups

```
backup                # Create manual backup
restore backup_name   # Restore a backup
```

### Utility

```
help                  # Show help
history               # Show command history
clear                 # Clear screen
exit                  # Exit Orchestra
```

## 🎯 Use Cases

### Bug Fixing
```powershell
orchestra> Fix the authentication bug in auth.py
```

### Feature Addition
```powershell
orchestra> Add rate limiting to all API endpoints
```

### Refactoring
```powershell
orchestra> Convert UserService to use async/await
```

### Code Review
```powershell
orchestra> Review this for security issues !review
```

## 🔒 Safety Features

### Automatic Backups
Before applying any changes, Orchestra automatically creates a timestamped backup. You can always roll back if something goes wrong.

### Diff Previews
See exactly what will change before applying:
```diff
+ def new_function():
+     pass
- def old_function():
-     pass
```

### Dry Run Mode
Preview changes without applying them:
```powershell
python -m orchestra --dry-run
```

## 📊 How It Works

1. **You provide a prompt** - Describe what you want to do
2. **Context gathering** - Orchestra scans your codebase for context
3. **Parallel execution** - All AI agents work simultaneously
4. **Peer evaluation** - Agents evaluate each other's solutions
5. **Ranked results** - Solutions are ranked by quality
6. **Interactive selection** - You preview and choose the best solution
7. **Safe application** - Automatic backup, then apply changes

## 🛠️ Advanced Usage

### Specify Working Directory
```powershell
cd ./my-project
orchestra
```

### From Anywhere
```powershell
# Set working directory from within Orchestra
orchestra> cd D:\my-project
orchestra> Refactor API
```

### Skip Context
For faster responses on small tasks:
```powershell
orchestra> set nocontext
orchestra> Quick function fix
```

## 💡 Tips

1. **Be specific** - More detailed prompts get better results
2. **Use context** - Let Orchestra scan your codebase for better solutions
3. **Review diffs** - Always check what will change before applying
4. **Keep backups** - Don't clean old backups too quickly
5. **Experiment** - Try different agents for different tasks

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🔗 Links

- [Documentation](USAGE_GUIDE.md)
- [Implementation Details](IMPLEMENTATION_COMPLETE.md)
- [Report Issues](https://github.com/your-username/orchestra/issues)

## 🙏 Acknowledgments

- Built with [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Uses [Questionary](https://questionary.readthedocs.io/) for interactive prompts
- Powered by your favorite AI CLI tools (Claude, Gemini, OpenAI)

---

**Happy coding with your AI team!** 🎉🚀
