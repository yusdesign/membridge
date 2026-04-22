---
layout: default
title: MemBridge - Termux Memory Palace
description: Zero-dependency memory system for Termux AI assistants
---

# 🏛️ MemBridge

<p align="center">
  <img src="../assets/logo.svg" alt="MemBridge Logo" width="500"/>
</p>

**Termux-native memory palace for AI assistants**

[Quick Start](quickstart) • [Documentation](usage) • [GitHub](https://github.com/yusdesign/membridge)

## What is MemBridge?

MemBridge is a **pure SQLite3** memory system that runs in Termux. It indexes your entire Termux home directory and provides instant full-text search over all your projects, scripts, and documentation.

### Perfect for AI Assistants

Paste `membridge wake-up` to DeepSeek, Claude, or ChatGPT, and they instantly know:
- Every project you've built
- Every script you've written
- Every README you've documented

**No more repeating yourself. Your AI remembers everything.**

## Features

| Feature | Description |
|---------|-------------|
| 🪶 **Zero Dependencies** | Only Python's built-in sqlite3 |
| ⚡ **FTS5 Search** | Google-like full-text search |
| 🏛️ **Palace Structure** | MemPalace-compatible wings/rooms/halls |
| 📦 **Git Integration** | Auto-discovers repositories |
| 🐍 **Python Projects** | Detects requirements.txt, setup.py |
| 🔒 **100% Local** | No cloud, no telemetry |

## Performance

- **1,500 files** indexed in < 30 seconds
- **Search latency** < 10ms
- **Database size** ~5MB for 1,500 files
- **RAM usage** < 50MB

## Get Started

```bash
curl -sSL https://raw.githubusercontent.com/yusdesign/membridge/main/install.sh | bash
membridge mine
membridge search "your project"
```

Read the full [Quick Start](quickstart) →
