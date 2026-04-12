#!/usr/bin/env python3
"""
Termux-native Memory Bridge - Pure SQLite3
Zero native dependencies, works on any Python 3.6+
"""
import os
import json
import sqlite3
import subprocess
import hashlib
import re
from pathlib import Path
from datetime import datetime
from collections import Counter
from typing import Dict, List, Optional, Tuple

class TermuxMemPalace:
    """Pure SQLite3 memory system - 100% Termux compatible"""
    
    def __init__(self, palace_path=None):
        if palace_path is None:
            palace_path = Path.home() / ".mempalace"
        
        self.palace_path = Path(palace_path)
        self.palace_path.mkdir(parents=True, exist_ok=True)
        
        # Termux paths
        self.termux_home = Path.home()
        self.termux_storage = Path.home() / "storage" / "shared"
        
        # Initialize
        self._init_config()
        self._init_database()
        
        # Stats
        self.mining_stats = {
            "git_repos": 0, "python_projects": 0, "scripts": 0,
            "configs": 0, "documents": 0, "notes": 0
        }
    
    def _init_config(self):
        """Initialize configuration"""
        config_file = self.palace_path / "config.json"
        if not config_file.exists():
            config = {
                "palace_path": str(self.palace_path),
                "termux_home": str(self.termux_home),
                "termux_storage": str(self.termux_storage),
                "version": "pure-sqlite-3.0",
                "mining_excludes": [".cache", ".npm", ".cargo", ".local", "tmp", "__pycache__", ".git"],
                "text_extensions": [".py", ".sh", ".md", ".txt", ".json", ".yaml", ".yml", 
                                   ".js", ".html", ".css", ".xml", ".ini", ".conf", ".cfg"]
            }
            config_file.write_text(json.dumps(config, indent=2))
        
        self.config = json.loads(config_file.read_text())
        
        # Identity file
        identity_file = self.palace_path / "identity.txt"
        if not identity_file.exists():
            identity = f"Termux User\nHome: {self.termux_home}\nMemory: Pure SQLite3"
            identity_file.write_text(identity)
    
    def _init_database(self):
        """Initialize SQLite database with full-text search"""
        db_path = self.palace_path / "memory.db"
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        
        # Enable full-text search
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        
        # Main memories table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wing TEXT NOT NULL,
                room TEXT NOT NULL,
                hall TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                content_hash TEXT UNIQUE,
                file_path TEXT,
                file_type TEXT,
                line_count INTEGER,
                keywords TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # FTS5 virtual table for lightning-fast search
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                title, content, wing, room, hall, file_path,
                content=memories, content_rowid=id
            )
        """)
        
        # Triggers to keep FTS in sync
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, title, content, wing, room, hall, file_path)
                VALUES (new.id, new.title, new.content, new.wing, new.room, new.hall, new.file_path);
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, title, content, wing, room, hall, file_path)
                VALUES ('delete', old.id, old.title, old.content, old.wing, old.room, old.hall, old.file_path);
            END
        """)
        
        self.conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, title, content, wing, room, hall, file_path)
                VALUES ('delete', old.id, old.title, old.content, old.wing, old.room, old.hall, old.file_path);
                INSERT INTO memories_fts(rowid, title, content, wing, room, hall, file_path)
                VALUES (new.id, new.title, new.content, new.wing, new.room, new.hall, new.file_path);
            END
        """)
        
        # Knowledge graph triples
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS triples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                valid_from TEXT,
                valid_until TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Relationships between memories
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                target_id INTEGER,
                relation_type TEXT,
                weight REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES memories(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES memories(id) ON DELETE CASCADE
            )
        """)
        
        # Mining history
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS mining_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                files_found INTEGER,
                files_indexed INTEGER,
                status TEXT,
                mined_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for speed
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_wing ON memories(wing)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_room ON memories(room)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_hall ON memories(hall)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_file_path ON memories(file_path)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at)")
        
        self.conn.commit()
    
    def add_memory(self, content, wing="general", room="default", hall="events",
                   title=None, file_path=None, file_type=None, metadata=None):
        """Add a memory to SQLite"""
        
        # Generate hash for deduplication
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Check if exists
        existing = self.conn.execute(
            "SELECT id FROM memories WHERE content_hash = ?",
            (content_hash,)
        ).fetchone()
        
        if existing:
            return existing['id']
        
        # Extract title if not provided
        if not title:
            lines = content.strip().split('\n')
            title = lines[0][:100] if lines else "Untitled"
        
        # Extract keywords for better search
        keywords = self._extract_keywords(content)
        
        # Line count
        line_count = len(content.split('\n'))
        
        # Insert
        cursor = self.conn.execute("""
            INSERT INTO memories 
            (wing, room, hall, title, content, content_hash, file_path, 
             file_type, line_count, keywords, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wing, room, hall, title, content, content_hash,
            file_path, file_type, line_count, ','.join(keywords),
            json.dumps(metadata or {}), datetime.now().isoformat()
        ))
        
        memory_id = cursor.lastrowid
        self.conn.commit()
        
        return memory_id
    
    def _extract_keywords(self, text: str, limit: int = 20) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]{2,}\b', text.lower())
        
        # Common stopwords
        stopwords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 
                     'have', 'has', 'are', 'were', 'was', 'not', 'but', 'you',
                     'your', 'can', 'all', 'will', 'what', 'when', 'where'}
        
        # Count frequencies
        word_counts = Counter(w for w in words if w not in stopwords)
        
        # Return top keywords
        return [word for word, _ in word_counts.most_common(limit)]
    
    def search(self, query: str, wing: str = None, room: str = None, 
               hall: str = None, limit: int = 10) -> List[Dict]:
        """Search using SQLite FTS5"""
        
        # Build WHERE clause
        where_parts = []
        params = []
        
        if wing:
            where_parts.append("wing = ?")
            params.append(wing)
        if room:
            where_parts.append("room = ?")
            params.append(room)
        if hall:
            where_parts.append("hall = ?")
            params.append(hall)
        
        where_clause = " AND ".join(where_parts) if where_parts else "1=1"
        
        # FTS5 search with ranking
        sql = f"""
            SELECT 
                m.id, m.wing, m.room, m.hall, m.title, m.content,
                m.file_path, m.file_type, m.keywords, m.created_at,
                highlight(memories_fts, 1, '<b>', '</b>') as title_highlight,
                snippet(memories_fts, 2, '<b>', '</b>', '...', 30) as content_snippet,
                rank
            FROM memories_fts 
            JOIN memories m ON m.id = memories_fts.rowid
            WHERE memories_fts MATCH ? AND {where_clause}
            ORDER BY rank
            LIMIT ?
        """
        
        # FTS5 query syntax
        fts_query = self._build_fts_query(query)
        params.insert(0, fts_query)
        params.append(limit)
        
        results = []
        for row in self.conn.execute(sql, params):
            results.append({
                'id': row['id'],
                'wing': row['wing'],
                'room': row['room'],
                'hall': row['hall'],
                'title': row['title'],
                'content': row['content'][:500],
                'snippet': row['content_snippet'],
                'highlight': row['title_highlight'],
                'file_path': row['file_path'],
                'file_type': row['file_type'],
                'keywords': row['keywords'],
                'created_at': row['created_at'],
                'rank': row['rank']
            })
        
        return results
    
    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query from user input"""
        # Split and clean terms
        terms = re.findall(r'\w+', query.lower())
        
        # Use OR for multiple terms
        if len(terms) > 1:
            return ' OR '.join(terms)
        return query
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[Dict]:
        """Search by keyword matching"""
        keyword_pattern = '%' + '%'.join(keywords) + '%'
        
        sql = """
            SELECT id, wing, room, hall, title, content, file_path, created_at
            FROM memories
            WHERE keywords LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        """
        
        results = []
        for row in self.conn.execute(sql, (keyword_pattern, limit)):
            results.append(dict(row))
        
        return results
    
    def mine_termux_home(self, scan_depth: int = 3) -> Dict:
        """Mine Termux home directory"""
        
        exclude = self.config.get("mining_excludes", [])
        text_exts = self.config.get("text_extensions", [])
        
        print(f"🔍 Mining Termux home: {self.termux_home}")
        print(f"   Text extensions: {', '.join(text_exts[:5])}...")
        print("=" * 50)
        
        # Reset stats
        for key in self.mining_stats:
            self.mining_stats[key] = 0
        
        # Find and index content
        all_files = self._find_text_files(self.termux_home, scan_depth, exclude, text_exts)
        
        for file_path in all_files:
            self._index_file(file_path)
        
        # Special: find git repos
        git_repos = self._find_git_repos(self.termux_home, scan_depth, exclude)
        for repo in git_repos:
            self._mine_git_repo(repo)
            self.mining_stats["git_repos"] += 1
        
        # Special: find python projects
        py_projects = self._find_python_projects(self.termux_home, scan_depth, exclude)
        for proj in py_projects:
            self._mine_python_project(proj)
            self.mining_stats["python_projects"] += 1
        
        # Record mining session
        total = sum(self.mining_stats.values())
        self.conn.execute("""
            INSERT INTO mining_history (path, files_found, files_indexed, status)
            VALUES (?, ?, ?, ?)
        """, (str(self.termux_home), len(all_files), total, "completed"))
        self.conn.commit()
        
        print("=" * 50)
        print(f"✅ Indexed {total} items from {len(all_files)} files")
        
        return self.mining_stats
    
    def _find_text_files(self, path: Path, depth: int, exclude: List[str], 
                         extensions: List[str]) -> List[Path]:
        """Find all text files recursively"""
        files = []
        
        try:
            for item in path.iterdir():
                # Skip excluded
                if any(ex in str(item) for ex in exclude):
                    continue
                
                if item.is_file():
                    # Check extension
                    if item.suffix in extensions:
                        files.append(item)
                    # Also check files without extension but likely text
                    elif not item.suffix and item.stat().st_size < 100000:
                        # Try to detect if text
                        try:
                            item.read_text()[:100]
                            files.append(item)
                        except:
                            pass
                
                elif item.is_dir() and depth > 0:
                    files.extend(self._find_text_files(item, depth - 1, exclude, extensions))
        
        except PermissionError:
            pass
        
        return files
    
    def _find_git_repos(self, path: Path, depth: int, exclude: List[str]) -> List[Path]:
        """Find git repositories"""
        repos = []
        
        try:
            for item in path.iterdir():
                if any(ex in str(item) for ex in exclude):
                    continue
                
                if item.is_dir() and not item.name.startswith('.'):
                    if (item / ".git").exists():
                        repos.append(item)
                    elif depth > 0:
                        repos.extend(self._find_git_repos(item, depth - 1, exclude))
        
        except PermissionError:
            pass
        
        return repos
    
    def _find_python_projects(self, path: Path, depth: int, exclude: List[str]) -> List[Path]:
        """Find Python projects"""
        projects = []
        markers = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', '__init__.py']
        
        try:
            for item in path.iterdir():
                if any(ex in str(item) for ex in exclude):
                    continue
                
                if item.is_dir() and not item.name.startswith('.'):
                    if any((item / m).exists() for m in markers):
                        projects.append(item)
                    elif depth > 0:
                        projects.extend(self._find_python_projects(item, depth - 1, exclude))
        
        except PermissionError:
            pass
        
        return projects
    
    def _index_file(self, file_path: Path) -> Optional[int]:
        """Index a single file"""
        
        try:
            content = file_path.read_text()
            
            # Skip if too large (>1MB)
            if len(content) > 1000000:
                return None
            
            # Determine wing based on path
            wing = self._determine_wing(file_path)
            room = self._determine_room(file_path)
            hall = self._determine_hall(file_path)
            
            # Count for stats
            if file_path.suffix == '.py' or file_path.suffix == '.sh':
                self.mining_stats["scripts"] += 1
            elif file_path.suffix in ['.json', '.yaml', '.yml', '.conf', '.ini']:
                self.mining_stats["configs"] += 1
            elif file_path.suffix in ['.md', '.txt']:
                self.mining_stats["documents"] += 1
            else:
                self.mining_stats["notes"] += 1
            
            # Add memory
            memory_id = self.add_memory(
                content=content,
                wing=wing,
                room=room,
                hall=hall,
                title=file_path.name,
                file_path=str(file_path),
                file_type=file_path.suffix[1:] if file_path.suffix else "text",
                metadata={"size": len(content)}
            )
            
            # Link to related files in same directory
            self._link_related_files(file_path, memory_id)
            
            if memory_id and len(content) > 0:
                # Show progress for significant files
                if 'README' in file_path.name or file_path.suffix == '.py':
                    print(f"   📄 {file_path.relative_to(self.termux_home)}")
            
            return memory_id
            
        except Exception as e:
            return None
    
    def _determine_wing(self, file_path: Path) -> str:
        """Determine wing based on file location"""
        rel_path = str(file_path.relative_to(self.termux_home))
        
        if 'storage/shared' in rel_path:
            return "storage"
        elif 'projects' in rel_path or 'git' in rel_path:
            return "projects"
        elif 'scripts' in rel_path or 'bin' in rel_path:
            return "scripts"
        elif '.config' in rel_path or '.termux' in rel_path:
            return "configs"
        else:
            return "home"
    
    def _determine_room(self, file_path: Path) -> str:
        """Determine room based on parent directory"""
        parent = file_path.parent.name
        if parent and parent != '.':
            return parent
        return "root"
    
    def _determine_hall(self, file_path: Path) -> str:
        """Determine hall based on file type"""
        ext = file_path.suffix
        
        type_map = {
            '.py': 'code',
            '.sh': 'scripts',
            '.md': 'docs',
            '.txt': 'notes',
            '.json': 'data',
            '.yaml': 'config',
            '.yml': 'config',
            '.conf': 'config',
            '.ini': 'config'
        }
        
        return type_map.get(ext, 'files')
    
    def _link_related_files(self, file_path: Path, memory_id: int):
        """Link to other files in same directory"""
        parent = file_path.parent
        
        try:
            # Find other indexed files in same directory
            for sibling in parent.iterdir():
                if sibling == file_path:
                    continue
                
                # Find memory ID of sibling
                sibling_row = self.conn.execute(
                    "SELECT id FROM memories WHERE file_path = ?",
                    (str(sibling),)
                ).fetchone()
                
                if sibling_row:
                    # Create bidirectional relation
                    self.conn.execute("""
                        INSERT OR IGNORE INTO relations (source_id, target_id, relation_type)
                        VALUES (?, ?, 'same_directory')
                    """, (memory_id, sibling_row['id']))
        except:
            pass
    
    def _mine_git_repo(self, repo_path: Path):
        """Index git repository metadata"""
        name = repo_path.name
        
        # Get git info
        try:
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'log', '-1', '--format=%s|%an|%ad'],
                capture_output=True, text=True, timeout=5
            )
            last_commit = result.stdout.strip() if result.returncode == 0 else ""
        except:
            last_commit = ""
        
        # Get remote
        try:
            result = subprocess.run(
                ['git', '-C', str(repo_path), 'remote', 'get-url', 'origin'],
                capture_output=True, text=True, timeout=3
            )
            remote = result.stdout.strip() if result.returncode == 0 else "local"
        except:
            remote = "local"
        
        # Add to KG
        self.add_triple(f"repo:{name}", "type", "git_repository")
        self.add_triple(f"repo:{name}", "path", str(repo_path))
        self.add_triple(f"repo:{name}", "remote", remote)
        
        if last_commit:
            parts = last_commit.split('|')
            if len(parts) >= 1:
                self.add_triple(f"repo:{name}", "last_commit", parts[0][:100])
        
        print(f"   📦 {name}: {remote}")
    
    def _mine_python_project(self, proj_path: Path):
        """Index Python project metadata"""
        name = proj_path.name
        
        # Check requirements
        req_file = proj_path / "requirements.txt"
        deps = []
        if req_file.exists():
            deps = [l.strip() for l in req_file.read_text().splitlines() if l.strip()][:20]
        
        self.add_triple(f"project:{name}", "type", "python")
        self.add_triple(f"project:{name}", "path", str(proj_path))
        self.add_triple(f"project:{name}", "dependencies", str(len(deps)))
        
        if deps:
            self.add_triple(f"project:{name}", "top_deps", ', '.join(deps[:5]))
        
        print(f"   🐍 {name}: {len(deps)} dependencies")
    
    def add_triple(self, subject: str, predicate: str, object_: str):
        """Add knowledge graph triple"""
        self.conn.execute("""
            INSERT INTO triples (subject, predicate, object, valid_from)
            VALUES (?, ?, ?, ?)
        """, (subject, predicate, object_, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_related(self, memory_id: int, limit: int = 5) -> List[Dict]:
        """Get related memories"""
        sql = """
            SELECT m.* FROM memories m
            JOIN relations r ON m.id = r.target_id
            WHERE r.source_id = ?
            ORDER BY r.weight DESC
            LIMIT ?
        """
        
        results = []
        for row in self.conn.execute(sql, (memory_id, limit)):
            results.append(dict(row))
        
        return results
    
    def wake_up(self) -> str:
        """Generate context for DeepSeek"""
        identity = (self.palace_path / "identity.txt").read_text()
        
        context = []
        context.append("=== TERMUX MEMORY CONTEXT (SQLite) ===")
        context.append(f"Identity: {identity}")
        
        # Stats
        total = self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        triples = self.conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
        context.append(f"Total memories: {total}, Knowledge triples: {triples}")
        
        # Recent mining
        last_mine = self.conn.execute("""
            SELECT path, files_indexed, mined_at 
            FROM mining_history 
            ORDER BY mined_at DESC 
            LIMIT 1
        """).fetchone()
        
        if last_mine:
            context.append(f"\nLast mined: {last_mine['files_indexed']} files on {last_mine['mined_at'][:10]}")
        
        # Git repos
        repos = self.conn.execute("""
            SELECT DISTINCT subject, object 
            FROM triples 
            WHERE predicate = 'remote' 
            LIMIT 5
        """).fetchall()
        
        if repos:
            context.append("\n📦 Git repositories:")
            for r in repos:
                context.append(f"  • {r['subject']}: {r['object']}")
        
        # Python projects
        projects = self.conn.execute("""
            SELECT DISTINCT subject, object 
            FROM triples 
            WHERE predicate = 'type' AND object = 'python'
            LIMIT 5
        """).fetchall()
        
        if projects:
            context.append("\n🐍 Python projects:")
            for p in projects:
                context.append(f"  • {p['subject']}")
        
        # Recent memories
        recent = self.conn.execute("""
            SELECT wing, room, hall, title, file_path, created_at
            FROM memories 
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchall()
        
        context.append("\n📝 Recent indexed files:")
        for r in recent:
            context.append(f"  • [{r['wing']}/{r['room']}] {r['title']}")
        
        # Wings summary
        wings = self.conn.execute("""
            SELECT wing, COUNT(*) as count 
            FROM memories 
            GROUP BY wing 
            ORDER BY count DESC 
            LIMIT 5
        """).fetchall()
        
        context.append("\n📊 Memory distribution:")
        for w in wings:
            context.append(f"  • {w['wing']}: {w['count']} items")
        
        return "\n".join(context)
    
    def status(self) -> Dict:
        """Get palace status"""
        total = self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        triples = self.conn.execute("SELECT COUNT(*) FROM triples").fetchone()[0]
        relations = self.conn.execute("SELECT COUNT(*) FROM relations").fetchone()[0]
        
        # File types
        file_types = self.conn.execute("""
            SELECT file_type, COUNT(*) as count 
            FROM memories 
            WHERE file_type IS NOT NULL
            GROUP BY file_type 
            ORDER BY count DESC 
            LIMIT 10
        """).fetchall()
        
        return {
            "palace_path": str(self.palace_path),
            "database_size": (self.palace_path / "memory.db").stat().st_size // 1024,
            "total_memories": total,
            "total_triples": triples,
            "total_relations": relations,
            "file_types": [f"{ft['file_type']}: {ft['count']}" for ft in file_types]
        }
    
    def vacuum(self):
        """Optimize database"""
        self.conn.execute("INSERT INTO memories_fts(memories_fts) VALUES('optimize')")
        self.conn.execute("VACUUM")
        self.conn.commit()


# CLI
if __name__ == "__main__":
    import sys
    
    palace = TermuxMemPalace()
    
    if len(sys.argv) < 2:
        print("Termux SQLite Memory Bridge")
        print("\nCommands:")
        print("  mine              - Index Termux home")
        print("  search <query>    - Full-text search")
        print("  add <text>        - Add memory")
        print("  wake-up           - Get context for AI")
        print("  status            - Show stats")
        print("  vacuum            - Optimize database")
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "mine":
        stats = palace.mine_termux_home()
        print(f"\n📊 Mining complete!")
        print(f"   Git repos: {stats['git_repos']}")
        print(f"   Python projects: {stats['python_projects']}")
        print(f"   Scripts: {stats['scripts']}")
        print(f"   Configs: {stats['configs']}")
        print(f"   Documents: {stats['documents']}")
        print(f"   Other: {stats['notes']}")
        print(f"   Total: {sum(stats.values())}")
    
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python bridge.py search <query>")
            sys.exit(1)
        
        query = " ".join(sys.argv[2:])
        results = palace.search(query)
        
        if results:
            print(f"\n🔍 Found {len(results)} results for '{query}':\n")
            for i, r in enumerate(results, 1):
                print(f"{i}. [{r['wing']}/{r['room']}] {r['title']}")
                if r['snippet']:
                    print(f"   {r['snippet']}")
                if r['file_path']:
                    print(f"   📁 {r['file_path']}")
                print()
        else:
            print(f"No results for '{query}'")
    
    elif cmd == "add":
        if len(sys.argv) < 3:
            print("Usage: python bridge.py add <text>")
            sys.exit(1)
        
        text = " ".join(sys.argv[2:])
        memory_id = palace.add_memory(text, hall="manual")
        print(f"✅ Added memory #{memory_id}")
    
    elif cmd == "wake-up":
        print(palace.wake_up())
    
    elif cmd == "status":
        status = palace.status()
        print("=== SQLITE MEMORY BRIDGE ===")
        for k, v in status.items():
            if isinstance(v, list):
                print(f"{k}:")
                for item in v:
                    print(f"  • {item}")
            else:
                print(f"{k}: {v}")
    
    elif cmd == "vacuum":
        palace.vacuum()
        print("✅ Database optimized")
    
    else:
        print(f"Unknown command: {cmd}")
