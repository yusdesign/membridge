---
layout: default
title: Architecture - MemBridge
description: How MemBridge works under the hood
---

# 🏗️ Architecture

MemBridge is designed for **simplicity, speed, and zero dependencies**.

## Core Principles

1. **Pure Python** - Only standard library
2. **SQLite Native** - Built-in FTS5, JSON, WAL mode
3. **MemPalace Compatible** - Same conceptual model
4. **Termux First** - Optimized for Android/Linux

## System Overview

```

┌───────────────────────────────────────────────────────┐
│                    Termux Environment                 │
├───────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐       ┌──────────────────────────┐  │
│  │   CLI Layer  │ ───▶ │   TermuxMemPalace Class  │  │
│  │  (Commands)  │       │      (Core Engine)       │  │
│  └──────────────┘       └────────────┬─────────────┘  │
│                                      │                │
│                                      ▼                │
│  ┌─────────────────────────────────────────────────┐  │
│  │              SQLite Database                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │  │
│  │  │  memories   │  │  triples    │  │relations│  │  │
│  │  │   (FTS5)    │  │    (KG)     │  │ (graph) │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────┘  │  │
│  └─────────────────────────────────────────────────┘  │
│                                      │                │
│                                      ▼                │
│  ┌─────────────────────────────────────────────────┐  │
│  │           Termux Home Directory                 │  │
│  │  ~/projects/  ~/scripts/  ~/storage/shared/     │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘

```

## Data Model

### Memories Table

The core storage for all indexed content:

```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    wing TEXT,           -- Project/domain (e.g., "radio", "dihedral")
    room TEXT,           -- Sub-topic (e.g., "circuits", "research")
    hall TEXT,           -- Memory type (e.g., "code", "docs", "config")
    title TEXT,          -- Filename or derived title
    content TEXT,        -- Full file content
    content_hash TEXT,   -- MD5 for deduplication
    file_path TEXT,      -- Original file location
    file_type TEXT,      -- Extension (py, md, sh, etc.)
    line_count INTEGER,  -- Number of lines
    keywords TEXT,       -- Extracted keywords (comma-separated)
    metadata TEXT,       -- JSON metadata
    created_at TEXT,
    updated_at TEXT
);
```

FTS5 Virtual Table

Enables Google-like full-text search:

```sql
CREATE VIRTUAL TABLE memories_fts USING fts5(
    title, content, wing, room, hall, file_path,
    content=memories, content_rowid=id
);
```

Key Features:

· BM25 ranking - Relevance scoring
· Prefix searches - auth* finds authentication, authorize
· Boolean operators - database AND (postgres OR sqlite)
· Phrase matching - "exact phrase match"
· NEAR queries - term NEAR/5 other

Knowledge Graph Triples

Entity-relationship storage:

```sql
CREATE TABLE triples (
    id INTEGER PRIMARY KEY,
    subject TEXT,      -- Entity (repo:myapp, project:tools)
    predicate TEXT,    -- Relationship (type, remote, path)
    object TEXT,       -- Value (python, https://..., /path)
    valid_from TEXT,   -- Temporal validity start
    valid_until TEXT,  -- Temporal validity end
    created_at TEXT
);
```

Example Triples:

```
subject           | predicate | object
------------------|-----------|--------
repo:myapp        | type      | git_repository
repo:myapp        | remote    | https://github.com/user/myapp
project:tools     | type      | python
project:tools     | deps_count| 12
file:main.py      | imports   | flask
file:main.py      | defines   | create_app
```

Relations Table

Links between memories:

```sql
CREATE TABLE relations (
    id INTEGER PRIMARY KEY,
    source_id INTEGER,    -- Source memory
    target_id INTEGER,    -- Related memory
    relation_type TEXT,   -- "same_directory", "imports", "references"
    weight REAL,          -- Relationship strength
    FOREIGN KEY (source_id) REFERENCES memories(id),
    FOREIGN KEY (target_id) REFERENCES memories(id)
);
```

Mining Process

1. Discovery Phase

```python
def mine_termux_home():
    # Find all text files
    files = _find_text_files(home_path)
    
    # Find git repositories
    repos = _find_git_repos(home_path)
    
    # Find Python projects
    projects = _find_python_projects(home_path)
```

2. Indexing Phase

For each file:

1. Read content (up to 1MB limit)
2. Extract metadata (path, type, size)
3. Determine structure (wing/room/hall based on location)
4. Extract keywords (simple TF-IDF-like extraction)
5. Store in SQLite (with deduplication)
6. Add to FTS5 (automatic via triggers)
7. Create relations (link to siblings)

3. Knowledge Extraction

For git repos:

· Extract remote URL
· Get last commit message
· Create triple: repo:name → remote → url

For Python projects:

· Parse requirements.txt
· Count dependencies
· Create triple: project:name → deps_count → N

Search Algorithm

1. Query Processing

```python
def search(query, wing=None, room=None, hall=None):
    # Build FTS5 query
    fts_query = _build_fts_query(query)
    # "database auth" → "database OR auth"
    
    # Execute with BM25 ranking
    results = conn.execute("""
        SELECT *, rank
        FROM memories_fts
        WHERE memories_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, [fts_query, limit])
```

2. Ranking

SQLite FTS5 uses BM25 algorithm:

```
BM25(d, q) = Σ IDF(qi) * (f(qi,d) * (k1+1)) / (f(qi,d) + k1*(1-b+b*|d|/avgdl))
```

Where:

· f(qi,d) = term frequency
· |d| = document length
· avgdl = average document length
· k1, b = tuning parameters

3. Snippet Generation

```sql
snippet(memories_fts, 2, '<b>', '</b>', '...', 30)
```

Generates context-aware snippets with highlighting.

Performance Optimizations

1. WAL Mode

```sql
PRAGMA journal_mode=WAL;
```

· Concurrent read/write
· Faster transactions
· Better for Termux storage

2. Indexes

```sql
CREATE INDEX idx_memories_wing ON memories(wing);
CREATE INDEX idx_memories_room ON memories(room);
CREATE INDEX idx_memories_hall ON memories(hall);
CREATE INDEX idx_memories_created ON memories(created_at);
```

3. Content Deduplication

```python
content_hash = hashlib.md5(content.encode()).hexdigest()
# Skip if already indexed
```

4. Batch Processing

Files are processed sequentially but with:

· Early skip for large files
· Binary detection (skip non-text)
· Permission error handling

Memory Palace Structure Mapping

MemPalace Concept MemBridge Implementation
Palace ~/.mempalace/memory.db
Wing Project or top-level directory
Room Subdirectory or topic
Hall File type (code, docs, config)
Closet File metadata
Drawer Actual file content
Tunnel Relations table linking files

Limitations & Trade-offs

Intentional Limitations

1. No vector embeddings - FTS5 is faster and zero-dependency
2. Text-only - No binary file parsing
3. Local only - No cloud sync (by design)
4. Simple keywords - No ML/NLP processing

Benefits of This Approach

· Zero dependencies - Works anywhere Python runs
· Instant search - FTS5 is incredibly fast
· Tiny footprint - Database is ~5MB for 1500 files
· Portable - Single .db file backup

Future Enhancements

· Semantic search via simple TF-IDF
· File change detection (auto-reindex)
· Export to MemPalace format
· Web UI for browsing
· Termux widget integration

---

☘️ Simple, fast, and always available.
