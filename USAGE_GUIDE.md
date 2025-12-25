# Multi-Agent Coder - Complete Usage Guide

## 🎉 New Features Overview

The Multi-Agent Coder now includes powerful new features:

1. **✅ True Parallel Execution** - All CLI tools run simultaneously
2. **📂 Working Directory Context** - Agents understand your codebase
3. **🔍 File Operations Detection** - Automatic detection of file changes
4. **📊 Interactive Solution Selection** - Choose the best solution with diff preview
5. **💾 Automatic Backups** - Safe changes with rollback capability

## 🚀 Quick Start Examples

### Basic Query with Context

```powershell
# Automatically uses current directory as context
python -m main_cli_new query "Add error handling to utils.py"
```

This will:
1. Scan your current directory
2. Provide file structure and important files to agents
3. Run all CLI tools in parallel
4. Let you preview and select the best solution

### Specify Working Directory

```powershell
# Analyze a specific project
python -m main_cli_new query "Refactor the authentication module" --cwd ./my-project
```

### Dry Run Mode

```powershell
# See what would change without actually modifying files
python -m main_cli_new query "Add logging to all functions" --dry-run
```

### Skip Context Gathering

```powershell
# Faster queries without codebase scanning
python -m main_cli_new query "Implement a linked list" --no-context
```

## 📋 Detailed Feature Usage

### 1. Working Directory Context

**What it does**: Scans your codebase to provide context to AI agents

**Information gathered**:
- Directory structure
- Project type detection (Python, Node.js, Go, etc.)
- Important configuration files
- README files
- Package files (package.json, requirements.txt, etc.)

**Usage**:
```powershell
# Auto-detect from current directory
python -m main_cli_new query "Add tests to utils.py"

# Specify directory
python -m main_cli_new query "Refactor API" --cwd ./backend

# Limit files scanned (for large projects)
python -m main_cli_new query "Optimize queries" --context-limit 5
```

### 2. Interactive Solution Selection

After receiving solutions from all agents, you'll see:

```
📊 Agent Solutions Ranked by Quality
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Rank ┃ Agent             ┃ Score  ┃ Time   ┃ Files            ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ 🥇 #1 │ Claude CLI        │ 70/100 │ 17.2s  │ 3 files         │
│ 🥈 #2 │ Gemini CLI        │ 32/100 │ 24.1s  │ 1 file          │
│ 🥉 #3 │ OpenAI CLI        │ 50/100 │ 0.7s   │ 2 files         │
└──────┴───────────────────┴────────┴────────┴─────────────────┘

Select a solution to preview:
  1. Claude CLI (Score: 70.0/100)
  2. Gemini CLI (Score: 32.5/100)
  3. OpenAI CLI (Score: 50.0/100)
  0. Cancel and exit
```

**Interactive Features**:
- View ranked solutions with scores
- See which files would be affected
- Preview diff before applying
- Choose to apply or cancel

### 3. File Operations Detection

The system automatically detects:
- ✨ **New files** to create
- ✏️ **Modifications** to existing files
- 🗑️ **Deletions** of files

**Example Output**:
```
📁 File Operations:
══════════════════════════════════════════════════════════════

✨ CREATE: binary_search.py
   Language: python
   Lines: 45
   Preview: def binary_search(arr, target):...

✏️ MODIFY: utils.py
   Language: python
   Lines: +12 -5
   Preview: def new_helper_function(data):...
```

### 4. Diff Viewer

Preview exactly what will change:

```
══════════════════════════════════════════════════════════════
File: binary_search.py (CREATE)
Lines: +45 -0
══════════════════════════════════════════════════════════════

+ def binary_search(arr, target):
+     left, right = 0, len(arr) - 1
+     while left <= right:
+         mid = (left + right) // 2
+         ...
```

### 5. Automatic Backups

Before applying any changes, the system:
1. Creates a timestamped backup
2. Stores all files that will be modified
3. Allows rollback if needed

**Backup management**:
```powershell
# List all backups
python -m main_cli_new backups --list

# Restore latest backup
python -m main_cli_new backups --restore backup_20231225_143022

# Keep only last 5 backups, clean old ones
python -m main_cli_new backups --count 5
```

## 📝 Complete Workflow Example

```powershell
# 1. Navigate to your project
cd D:\my-python-project

# 2. Run the query
python -m main_cli_new query "Add comprehensive error handling to all API endpoints"

# 3. System automatically:
#    ✓ Scans your project structure
#    ✓ Detects Python project type
#    ✓ Reads important files (requirements.txt, README.md, etc.)
#    ✓ Runs Claude, Gemini, and OpenAI in parallel
#    ✓ Evaluates responses

# 4. You see ranked solutions with file counts

# 5. Select solution 1 (Claude)

# 6. Preview changes with diff viewer

# 7. Confirm to apply

# 8. System:
#    ✓ Creates backup
#    ✓ Applies changes
#    ✓ Shows success summary
```

## 🎯 Common Use Cases

### Refactoring

```powershell
# Refactor with full project context
python -m main_cli_new query "Refactor UserService to use async/await" --cwd ./src
```

### Bug Fixing

```powershell
# Fix bug with context
python -m main_cli_new query "Fix the memory leak in the data processor" --cwd ./my-app
```

### Adding Features

```powershell
# Add new feature
python -m main_cli_new query "Add user authentication with JWT tokens"
```

### Code Review

```powershell
# Get multiple perspectives
python -m main_cli_new query "Review utils.py for bugs and improvements" --no-context
```

## ⚙️ All CLI Options

```powershell
python -m main_cli_new query [OPTIONS] PROMPT

Options:
  -i, --interactive          Interactive mode with clarifying questions
  -a, --agents TEXT          Comma-separated list of agents (e.g., claude,gemini)
  --skip-enhancement         Skip prompt enhancement
  -o, --output [CHOICE]      Output format: text or json
  --detect                   Run CLI detection first
  --cwd PATH                 Working directory for context
  --no-context               Skip codebase context gathering
  --context-limit INTEGER    Max files to include in context (default: 10)
  --dry-run                  Show what would happen without making changes
  --backup / --no-backup     Create backup before applying changes (default: True)
```

## 🛡️ Safety Features

### Backups

**Automatic backup creation**:
```powershell
# Before applying changes, you'll see:
💾 Creating backup...
✓ Backup created: .multi-agent-coder-backups/backup_20231225_143022
```

**Rollback**:
```powershell
# List backups
python -m main_cli_new backups --list

# Restore a backup
python -m main_cli_new backups --restore backup_20231225_143022
```

### Dry Run

Test without making changes:
```powershell
python -m main_cli_new query "Major refactoring" --dry-run
```

Shows what would change but doesn't modify files.

## 📊 Understanding the Output

### Ranking Table

```
Rank | Agent      | Score   | Time  | Files
─────┼────────────┼─────────┼───────┼───────
🥇#1  │ Claude CLI │ 70/100  │ 17.2s │ 3 files
```

**Ranking Criteria**:
- Peer evaluations (agents evaluating each other)
- Code quality
- Correctness
- Efficiency
- Best practices

### File Operations

```
✨ CREATE: new_file.py
   Language: python
   Lines: 45
   Preview: def function_name():...
```

**Symbols**:
- ✨ CREATE: New file will be created
- ✏️ MODIFY: Existing file will be updated
- 🗑️ DELETE: File will be removed

## 🔧 Troubleshooting

### No Context Gathered

```powershell
# If you see "No codebase context found"
python -m main_cli_new query "..." --no-context
```

### Backup Failed

```powershell
# Manually backup first
Copy-Item -Recurse ./my-project ./backup_before
python -m main_cli_new query "..." --no-backup
```

### Rollback Needed

```powershell
python -m main_cli_new backups --list
python -m main_cli_new backups --restore <backup-name>
```

## 💡 Tips

1. **Start Small**: Test with simple changes first
2. **Review Diffs**: Always check the diff before applying
3. **Use Dry Run**: Preview major changes with --dry-run
4. **Keep Backups**: Don't immediately clean up old backups
5. **Context Matters**: Use --cwd for better results
6. **Skip Context**: Use --no-context for faster queries on small tasks

## 🎓 Best Practices

1. **For large projects**: Use `--context-limit 5` to limit scanning
2. **For quick fixes**: Use `--skip-enhancement --no-context`
3. **Before major changes**: Always use `--dry-run` first
4. **For critical code**: Review diffs carefully, don't just accept the top score
5. **Regular backups**: Don't clean old backups too quickly

## 🚀 Advanced Usage

### Pipe Results

```powershell
# Get JSON output for scripting
python -m main_cli_new query "..." --output json > result.json
```

### Specific Agents

```powershell
# Use only Claude and Gemini
python -m main_cli_new query "..." --agents claude,gemini
```

### Interactive Mode

```powershell
# Full interactive experience
python -m main_cli_new query --interactive
```

This will:
1. Ask for your prompt
2. Ask clarifying questions
3. Run all agents
4. Show ranked solutions
5. Let you preview and select

---

**Happy Coding!** 🎉
