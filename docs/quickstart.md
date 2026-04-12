---
layout: default
title: Quick Start - MemBridge
description: Get started with MemBridge in 5 minutes
---

# 🚀 Quick Start

Get MemBridge running in your Termux environment in under 5 minutes.

## Prerequisites

- **Termux** installed on Android ([Get it here](https://termux.com))
- **Python 3.6+** (pre-installed in Termux)
- **Git** (optional, for cloning)

## Step 1: Install MemBridge

### Easy Install (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/yusdesign/membridge/main/install.sh | bash
```

Manual Install

```bash
git clone https://github.com/yusdesign/membridge.git
cd membridge
bash install.sh
```

Step 2: Mine Your Termux Home

```bash
# Reload shell to get the 'membridge' alias
source ~/.bashrc

# Start mining (this indexes everything in your Termux home)
membridge mine
```

Expected output:

```
🔍 Mining Termux home: /data/data/com.termux/files/home
==================================================
   📄 projects/myapp/README.md
   📄 scripts/deploy.sh
   📦 myproject: https://github.com/user/myproject.git
   🐍 myapp: 12 dependencies
==================================================
✅ Indexed 500 items from 480 files
```

Step 3: Search Your Memories

```bash
# Full-text search across all indexed files
membridge search "database"

# Search with filters
membridge search "auth" --wing myproject --hall code
```

Step 4: Connect to Your AI Assistant

For DeepSeek, Claude, or ChatGPT:

```bash
# Generate context
membridge wake-up

# Copy the output and paste it to your AI assistant
```

Example Output:

```
=== TERMUX MEMORY CONTEXT (SQLite) ===
Identity: Termux User
Total memories: 500, Knowledge triples: 42

📦 Git repositories:
  • repo:myproject: https://github.com/user/myproject

🐍 Python projects:
  • project:myapp

📝 Recent indexed files:
  • [projects/code] main.py
  • [scripts/bin] deploy.sh
```

For Local LLMs (Llama, Mistral):

```bash
# Save context to file
membridge wake-up > context.txt

# Feed to your local model
./llama-cli -f context.txt -p "What should we work on?"
```

Step 5: Keep It Updated

```bash
# Pull latest changes
cd ~/.membridge && git pull

# Re-index after major changes
membridge mine
```

What's Next?

· Complete Usage Guide - All commands and options
· Architecture - How MemBridge works
· API Reference - Python API documentation
· Examples - Real-world use cases

Troubleshooting

"membridge: command not found"

```bash
# Reload your shell
source ~/.bashrc

# Or use full path
python ~/.membridge/mempalace-bridge.py
```

"Permission denied" on install.sh

```bash
chmod +x install.sh
bash install.sh
```

Database locked error

```bash
# Wait a few seconds and retry, or:
membridge vacuum
```

Next Steps

Now that MemBridge is running, you can:

1. Star the repo ⭐ - github.com/yusdesign/membridge
2. Share your experience - Open a discussion
3. Contribute - Submit PRs for features you want

---

☘️ Welcome to the MemBridge community! Your AI assistant now remembers everything.
