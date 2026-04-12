---
layout: default
title: Complete Usage Guide - MemBridge
description: All commands and options for MemBridge
---

# 📚 Complete Usage Guide

MemBridge provides a simple but powerful CLI for managing your Termux memory palace.

## Command Reference

### `membridge mine`

Index your Termux home directory or a specific path.

```bash
# Index entire Termux home
membridge mine

# Index specific directory
membridge mine --path ~/myproject

# Index with custom depth
membridge mine --depth 5

# Exclude patterns
membridge mine --exclude "node_modules,.cache,tmp"
```

What gets indexed:

· Git repositories (with remote info)
· Python projects (requirements.txt, setup.py)
· Scripts (.py, .sh, .js, .rb)
· Configs (.json, .yaml, .toml, .ini)
· Documents (.md, .txt, .rst)
· All other text files

Output:

```
🔍 Mining Termux home: /data/data/com.termux/files/home
==================================================
   📄 projects/app/README.md
   📄 scripts/deploy.sh
   📦 myproject: https://github.com/user/repo.git
   🐍 app: 12 dependencies
==================================================
✅ Indexed 500 items from 480 files

📊 Mining complete!
   Git repos: 5
   Python projects: 3
   Scripts: 50
   Configs: 20
   Documents: 100
   Other: 322
   Total: 500
```

membridge search

Full-text search across all indexed content.

```bash
# Basic search
membridge search "authentication"

# Search with filters
membridge search "api" --wing myproject
membridge search "config" --hall config
membridge search "README" --room docs

# Limit results
membridge search "error" --limit 20

# Multiple filters
membridge search "database" --wing app --hall code --room models
```

Output:

```
🔍 Found 3 results for 'authentication':

1. [projects/app] auth.py
   ...def authenticate_user(username, password):...
   📁 ~/projects/app/auth.py

2. [configs/app] config.json
   ..."auth_endpoint": "https://api.example.com/auth"...
   📁 ~/configs/app/config.json

3. [docs/notes] README.md
   ...Authentication uses JWT tokens...
   📁 ~/docs/README.md
```

membridge wake-up

Generate context for AI assistants.

```bash
# Full context
membridge wake-up

# Context for specific wing
membridge wake-up --wing myproject

# Limit recent items
membridge wake-up --recent 20

# Export to file
membridge wake-up > ai_context.txt
```

Output format:

```
=== TERMUX MEMORY CONTEXT (SQLite) ===
Identity: Termux User
Home: /data/data/com.termux/files/home
Total memories: 500, Knowledge triples: 42

Last mined: 500 files on 2026-04-12

📦 Git repositories:
  • repo:app: https://github.com/user/app
  • repo:scripts: local

🐍 Python projects:
  • project:app
  • project:tools

📝 Recent indexed files:
  • [projects/code] main.py
  • [scripts/bin] deploy.sh

📊 Memory distribution:
  • home: 300 items
  • projects: 150 items
  • scripts: 50 items
```

membridge add

Manually add a memory.

```bash
# Basic memory
membridge add "Today I fixed the authentication bug"

# With structure
membridge add "Database migration completed" --wing app --room database --hall events

# From file
membridge add --file notes.txt --wing project --hall docs
```

membridge status

Show database statistics.

```bash
membridge status
```

Output:

```
=== SQLITE MEMORY BRIDGE ===
palace_path: /data/data/com.termux/files/home/.mempalace
database_size: 2048 KB
total_memories: 500
total_triples: 42
total_relations: 128
file_types:
  • py: 150
  • md: 100
  • json: 50
  • sh: 30
  • txt: 170
```

membridge vacuum

Optimize database.

```bash
# Run optimization
membridge vacuum
```

Advanced Features

Knowledge Graph Queries

```sql
# Direct SQLite access
sqlite3 ~/.mempalace/memory.db

# View all triples
SELECT * FROM triples LIMIT 10;

# Find all files in a wing
SELECT * FROM memories WHERE wing = 'myproject';

# Get file relationships
SELECT m1.title, m2.title 
FROM relations r
JOIN memories m1 ON r.source_id = m1.id
JOIN memories m2 ON r.target_id = m2.id
LIMIT 10;
```

Python API

```python
from mempalace_bridge import TermuxMemPalace

# Initialize
palace = TermuxMemPalace()

# Mine
palace.mine_termux_home()

# Search
results = palace.search("query")
for r in results:
    print(r['title'], r['snippet'])

# Add memory
palace.add_memory("Important note", wing="project")

# Add knowledge triple
palace.add_triple("user", "prefers", "dark_mode")

# Get context
context = palace.wake_up()
```

Automation

```bash
# Cron job for daily indexing (in Termux)
termux-job-scheduler \
  --script ~/.membridge/auto-mine.sh \
  --period-ms 86400000

# Git hook for auto-indexing
echo 'membridge mine --path .' > .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

Configuration

~/.mempalace/config.json

```json
{
  "palace_path": "/data/data/com.termux/files/home/.mempalace",
  "mining_excludes": [
    ".cache", ".npm", ".cargo",
    "node_modules", "__pycache__",
    ".git", "tmp"
  ],
  "text_extensions": [
    ".py", ".sh", ".md", ".txt",
    ".json", ".yaml", ".yml",
    ".js", ".html", ".css"
  ]
}
```

~/.mempalace/identity.txt

```
Your Name
Your Role
Your Preferences
```

Tips & Tricks

1. Speed Up Mining

```bash
# Exclude heavy directories
membridge mine --exclude "node_modules,.cache,tmp,downloads"
```

2. Focus on Active Projects

```bash
# Mine only what you need now
membridge mine --path ~/active-project
membridge wake-up --wing active-project
```

3. Keep Context Fresh

```bash
# Auto-wake-up alias
alias wake='membridge wake-up | pbcopy'  # macOS
alias wake='membridge wake-up | termux-clipboard-set'  # Termux
```

4. Search Shortcuts

```bash
# Add to .bashrc
alias ms='membridge search'
alias mw='membridge wake-up'
alias mm='membridge mine'
```

---

☘️ Happy memory keeping!
