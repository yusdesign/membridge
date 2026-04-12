---
layout: default
title: API Reference - MemBridge
description: Python API documentation for MemBridge
---

# 🔧 API Reference

MemBridge provides a clean Python API for programmatic access.

## TermuxMemPalace Class

### Constructor

```python
from mempalace_bridge import TermuxMemPalace

palace = TermuxMemPalace(palace_path=None)
```

Parameters:

· palace_path (str, optional): Custom palace location. Default: ~/.mempalace

Core Methods

mine_termux_home(scan_depth=3)

Index all content in Termux home directory.

```python
stats = palace.mine_termux_home(scan_depth=3)
print(f"Indexed {stats['total']} items")
```

Returns: Dictionary with mining statistics

```python
{
    "git_repos": 5,
    "python_projects": 3,
    "scripts": 50,
    "configs": 20,
    "documents": 100,
    "notes": 322
}
```

search(query, wing=None, room=None, hall=None, limit=10)

Full-text search across indexed memories.

```python
results = palace.search("authentication", wing="myproject", limit=5)
for r in results:
    print(r['title'], r['snippet'])
```

Parameters:

· query (str): Search query
· wing (str, optional): Filter by wing
· room (str, optional): Filter by room
· hall (str, optional): Filter by hall
· limit (int): Max results (default: 10)

Returns: List of memory dictionaries

```python
[{
    "id": 1,
    "wing": "myproject",
    "room": "auth",
    "hall": "code",
    "title": "auth.py",
    "content": "...",
    "snippet": "...<b>authentication</b>...",
    "file_path": "/path/to/file",
    "file_type": "py",
    "created_at": "2026-04-12T10:00:00",
    "rank": 0.95
}]
```

add_memory(content, wing="general", room="default", hall="events", **kwargs)

Manually add a memory.

```python
memory_id = palace.add_memory(
    content="Important discovery about kaleidoscopes",
    wing="kscope",
    room="research",
    hall="discoveries",
    title="Breakthrough",
    metadata={"importance": "high"}
)
```

Parameters:

· content (str): Memory content
· wing (str): Wing name
· room (str): Room name
· hall (str): Hall name
· title (str, optional): Memory title
· file_path (str, optional): Source file
· file_type (str, optional): File extension
· metadata (dict, optional): Additional metadata

Returns: memory_id (int)

add_triple(subject, predicate, object_, valid_from=None)

Add knowledge graph triple.

```python
palace.add_triple(
    "user", 
    "prefers", 
    "dark_mode",
    valid_from="2026-04-12"
)
```

Parameters:

· subject (str): Entity name
· predicate (str): Relationship type
· object_ (str): Target value
· valid_from (str, optional): ISO timestamp

wake_up(wing=None, recent=10)

Generate context for AI assistants.

```python
context = palace.wake_up(wing="myproject", recent=20)
print(context)
```

Parameters:

· wing (str, optional): Focus on specific wing
· recent (int): Number of recent memories (default: 10)

Returns: Formatted context string

status()

Get palace statistics.

```python
stats = palace.status()
print(f"Total memories: {stats['total_memories']}")
```

Returns: Dictionary with statistics

```python
{
    "palace_path": "/path/to/palace",
    "database_size": 2048,  # KB
    "total_memories": 500,
    "total_triples": 42,
    "total_relations": 128,
    "file_types": ["py: 150", "md: 100", ...]
}
```

vacuum()

Optimize database.

```python
palace.vacuum()
```

Utility Functions

_find_text_files(path, depth, exclude, extensions)

Internal: Find all text files recursively.

```python
files = palace._find_text_files(
    path=Path("/home"),
    depth=3,
    exclude=[".git", "node_modules"],
    extensions=[".py", ".md", ".txt"]
)
```

_extract_keywords(text, limit=20)

Internal: Extract keywords from text.

```python
keywords = palace._extract_keywords(
    "This is a sample text about databases and SQL",
    limit=5
)
# Returns: ["databases", "sql", "sample", "text", "about"]
```

Examples

1. Custom Mining

```python
from mempalace_bridge import TermuxMemPalace
from pathlib import Path

palace = TermuxMemPalace()

# Mine only specific directories
for project in ["~/radio", "~/dihedral", "~/kscope"]:
    path = Path(project).expanduser()
    for file in path.rglob("*.py"):
        palace._index_file(file)

print(f"Indexed specialized projects")
```

2. Search and Analyze

```python
# Find all files mentioning a concept
results = palace.search("kaleidoscope", limit=100)

# Group by wing
from collections import Counter
wings = Counter(r['wing'] for r in results)
print(f"Kaleidoscope appears in: {wings}")
```

3. Knowledge Graph Queries

```python
import sqlite3

conn = sqlite3.connect(palace.palace_path / "memory.db")

# Find all git remotes
for row in conn.execute(
    "SELECT subject, object FROM triples WHERE predicate = 'remote'"
):
    print(f"{row[0]}: {row[1]}")

# Find files with most relations
for row in conn.execute("""
    SELECT m.title, COUNT(*) as rel_count
    FROM memories m
    JOIN relations r ON m.id = r.source_id
    GROUP BY m.id
    ORDER BY rel_count DESC
    LIMIT 10
"""):
    print(f"{row['title']}: {row['rel_count']} relations")
```

4. AI Context Automation

```python
def get_project_context(project_name):
    """Get context for specific project"""
    palace = TermuxMemPalace()
    
    context = f"# Project: {project_name}\n\n"
    
    # Get project files
    files = palace.search(
        "", 
        wing=project_name, 
        limit=50
    )
    
    context += "## Files:\n"
    for f in files:
        context += f"- {f['title']}\n"
    
    # Get knowledge triples
    import sqlite3
    conn = sqlite3.connect(palace.palace_path / "memory.db")
    triples = conn.execute("""
        SELECT predicate, object 
        FROM triples 
        WHERE subject = ?
    """, [f"project:{project_name}"]).fetchall()
    
    if triples:
        context += "\n## Metadata:\n"
        for t in triples:
            context += f"- {t['predicate']}: {t['object']}\n"
    
    return context

# Usage
context = get_project_context("kscope")
print(context)
```

Error Handling

```python
try:
    palace = TermuxMemPalace()
    palace.mine_termux_home()
except sqlite3.OperationalError as e:
    print(f"Database error: {e}")
except PermissionError as e:
    print(f"Cannot access: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

☘️ Program with memory!
