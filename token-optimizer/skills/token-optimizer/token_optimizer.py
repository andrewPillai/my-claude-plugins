#!/usr/bin/env python3
"""
Token Optimizer CLI - Core logic for the token-optimizer skill.
This module provides the backend functionality for token optimization commands.
"""

import json
import os
import sys
import yaml
import argparse
import re
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import difflib

# ─── Paths ────────────────────────────────────────────────────────────────

def get_project_slug() -> str:
    """Get current project slug from cwd or environment."""
    cwd = Path.cwd()
    # Check for .claude directory in parents
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".claude").exists():
            return parent.name.lower().replace(" ", "-").replace("_", "-")
    return "default"

def get_memory_dir(project_slug: str = None) -> Path:
    """Get the memory directory for the current project."""
    if project_slug is None:
        project_slug = get_project_slug()
    base = Path.home() / ".claude" / "projects" / project_slug / "memory"
    base.mkdir(parents=True, exist_ok=True)
    return base

def get_mindmap_path(project_slug: str = None) -> Path:
    """Get the mind-map JSON path."""
    if project_slug is None:
        project_slug = get_project_slug()
    return get_memory_dir(project_slug).parent / "mindmap.json"

def get_config_path() -> Path:
    """Get the config file path."""
    return Path(__file__).parent.parent / "config.yaml"

# ─── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class Memory:
    name: str
    description: str
    metadata: Dict[str, Any]
    content: str = ""
    file_path: Optional[Path] = None

    @property
    def memory_type(self) -> str:
        return self.metadata.get("type", "fact")

    @property
    def tags(self) -> List[str]:
        return self.metadata.get("tags", [])

    @property
    def relevance(self) -> str:
        return self.metadata.get("relevance", "medium")

    @property
    def session(self) -> Optional[str]:
        return self.metadata.get("session")

@dataclass
class MindMapNode:
    id: str
    type: str  # concept, memory, file, task, external
    label: str
    description: str = ""
    tags: List[str] = None
    memories: List[str] = None
    files: List[str] = None
    relevance: str = "medium"
    status: str = "active"
    session: str = ""
    created: str = ""
    updated: str = ""

    def __post_init__(self):
        if self.tags is None: self.tags = []
        if self.memories is None: self.memories = []
        if self.files is None: self.files = []
        if not self.created:
            self.created = datetime.now().isoformat()
        self.updated = datetime.now().isoformat()

@dataclass
class MindMapEdge:
    from_id: str
    to_id: str
    type: str  # contains, relates-to, depends-on, supersedes, references, implements, documents
    weight: float = 1.0
    note: str = ""

@dataclass
class MindMap:
    version: int = 1
    nodes: Dict[str, MindMapNode] = None
    edges: List[MindMapEdge] = None
    updated: str = ""

    def __post_init__(self):
        if self.nodes is None: self.nodes = {}
        if self.edges is None: self.edges = []
        if not self.updated:
            self.updated = datetime.now().isoformat()


# ─── Session Activity Tracking ────────────────────────────────────────────────

@dataclass
class SessionActivity:
    """Tracks activity during a session for auto-extraction."""
    session_id: str
    start_time: str
    files_read: List[Dict] = field(default_factory=list)
    files_written: List[Dict] = field(default_factory=list)
    commands_run: List[Dict] = field(default_factory=list)
    decisions_noted: List[str] = field(default_factory=list)
    facts_noted: List[str] = field(default_factory=list)
    gotchas_noted: List[str] = field(default_factory=list)
    patterns_noted: List[str] = field(default_factory=list)
    references_noted: List[str] = field(default_factory=list)
    tool_calls: List[Dict] = field(default_factory=list)
    transcript_exchanges: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'SessionActivity':
        return cls(**data)


def get_session_log_path(project_slug: str = None) -> Path:
    """Get the session activity log path."""
    if project_slug is None:
        project_slug = get_project_slug()
    return get_memory_dir(project_slug).parent / "session_activity.json"


def load_session_activity(project_slug: str = None) -> SessionActivity:
    """Load session activity from JSON file."""
    path = get_session_log_path(project_slug)
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return SessionActivity.from_dict(data)
    # Create new session
    return SessionActivity(
        session_id=f"sess-{datetime.now():%Y%m%d-%H%M%S}",
        start_time=datetime.now().isoformat()
    )


def save_session_activity(activity: SessionActivity, project_slug: str = None):
    """Save session activity to JSON file."""
    path = get_session_log_path(project_slug)
    path.write_text(json.dumps(activity.to_dict(), indent=2))


def track_file_read(file_path: str, lines: int, tool: str, project_slug: str = None):
    """Track a file read operation."""
    activity = load_session_activity(project_slug)
    activity.files_read.append({
        "path": file_path,
        "lines": lines,
        "tool": tool,
        "timestamp": datetime.now().isoformat()
    })
    save_session_activity(activity, project_slug)


def track_file_write(file_path: str, lines: int, tool: str, project_slug: str = None):
    """Track a file write operation."""
    activity = load_session_activity(project_slug)
    activity.files_written.append({
        "path": file_path,
        "lines": lines,
        "tool": tool,
        "timestamp": datetime.now().isoformat()
    })
    save_session_activity(activity, project_slug)


def track_command(command: str, exit_code: int, project_slug: str = None):
    """Track a command execution."""
    activity = load_session_activity(project_slug)
    activity.commands_run.append({
        "command": command,
        "exit_code": exit_code,
        "timestamp": datetime.now().isoformat()
    })
    save_session_activity(activity, project_slug)


def track_tool_call(tool_name: str, args: Dict, result_summary: str, project_slug: str = None):
    """Track a tool call for token estimation."""
    activity = load_session_activity(project_slug)
    activity.tool_calls.append({
        "tool": tool_name,
        "args_summary": str(args)[:200],
        "result_summary": result_summary[:200],
        "timestamp": datetime.now().isoformat()
    })
    save_session_activity(activity, project_slug)


def track_transcript_exchange(user_msg: str, assistant_msg: str, project_slug: str = None):
    """Track a conversation exchange for pattern detection."""
    activity = load_session_activity(project_slug)
    activity.transcript_exchanges.append({
        "user": user_msg[:500],
        "assistant": assistant_msg[:500],
        "timestamp": datetime.now().isoformat()
    })
    # Keep only last 50 exchanges to limit size
    if len(activity.transcript_exchanges) > 50:
        activity.transcript_exchanges = activity.transcript_exchanges[-50:]
    save_session_activity(activity, project_slug)

# ─── Config ────────────────────────────────────────────────────────────────

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    return {}

# ─── Memory Operations ──────────────────────────────────────────────────────

def load_memories(project_slug: str = None) -> List[Memory]:
    """Load all memories from the memory directory."""
    memories = []
    memory_dir = get_memory_dir(project_slug)

    for md_file in memory_dir.glob("*.md"):
        if md_file.name == "MEMORY.md":
            continue
        try:
            content = md_file.read_text()
            # Parse frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    memories.append(Memory(
                        name=md_file.stem,
                        description=frontmatter.get("description", ""),
                        metadata=frontmatter.get("metadata", {}),
                        content=body,
                        file_path=md_file
                    ))
        except Exception as e:
            print(f"Warning: Failed to parse {md_file}: {e}", file=sys.stderr)

    return memories

def save_memory(memory: Memory, project_slug: str = None) -> Path:
    """Save a memory to the memory directory."""
    memory_dir = get_memory_dir(project_slug)
    file_path = memory_dir / f"{memory.name}.md"

    frontmatter = {
        "name": memory.name,
        "description": memory.description,
        "metadata": memory.metadata
    }

    content = "---\n" + yaml.dump(frontmatter, sort_keys=False) + "---\n\n" + memory.content
    file_path.write_text(content)

    # Update MEMORY.md index
    update_memory_index(memory_dir)

    return file_path

def update_memory_index(memory_dir: Path):
    """Update MEMORY.md index file."""
    index_path = memory_dir / "MEMORY.md"
    lines = ["# Memory Index\n", ""]

    for md_file in sorted(memory_dir.glob("*.md")):
        if md_file.name == "MEMORY.md":
            continue
        try:
            content = md_file.read_text()
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    desc = frontmatter.get("description", "No description")
                    lines.append(f"- [{md_file.stem}]({md_file.name}) — hook: {desc}")
        except Exception:
            pass

    index_path.write_text("\n".join(lines))

# ─── Mind-Map Operations ────────────────────────────────────────────────────

def load_mindmap(project_slug: str = None) -> MindMap:
    """Load mind-map from JSON file."""
    path = get_mindmap_path(project_slug)
    if path.exists():
        with open(path) as f:
            data = json.load(f)

        nodes = {}
        for k, v in data.get("nodes", {}).items():
            nodes[k] = MindMapNode(**v)

        edges = []
        for e in data.get("edges", []):
            edges.append(MindMapEdge(**e))

        return MindMap(
            version=data.get("version", 1),
            nodes=nodes,
            edges=edges,
            updated=data.get("updated", datetime.now().isoformat())
        )
    return MindMap()

def save_mindmap(mindmap: MindMap, project_slug: str = None):
    """Save mind-map to JSON file."""
    path = get_mindmap_path(project_slug)
    # Backup
    if path.exists():
        backup = path.with_suffix(".backup.json")
        backup.write_text(path.read_text())

    data = {
        "version": mindmap.version,
        "nodes": {k: asdict(v) for k, v in mindmap.nodes.items()},
        "edges": [asdict(e) for e in mindmap.edges],
        "updated": datetime.now().isoformat()
    }
    path.write_text(json.dumps(data, indent=2))

def add_concept(mindmap: MindMap, concept_id: str, label: str, description: str = "", tags: List[str] = None):
    """Add a concept node to the mind-map."""
    if concept_id in mindmap.nodes:
        return mindmap.nodes[concept_id]

    node = MindMapNode(
        id=concept_id,
        type="concept",
        label=label,
        description=description,
        tags=tags or []
    )
    mindmap.nodes[concept_id] = node
    return node

def add_memory_node(mindmap: MindMap, memory: Memory, concept_id: str = None):
    """Add a memory node and link to concept."""
    node = MindMapNode(
        id=memory.name,
        type="memory",
        label=memory.description or memory.name,
        description=memory.content[:500] if memory.content else "",
        tags=memory.tags,
        relevance=memory.relevance,
        session=memory.session or "",
        created=memory.metadata.get("timestamp", datetime.now().isoformat())
    )
    mindmap.nodes[memory.name] = node

    # Link to concept if provided
    if concept_id and concept_id in mindmap.nodes:
        mindmap.edges.append(MindMapEdge(
            from_id=concept_id,
            to_id=memory.name,
            type="contains"
        ))
        mindmap.nodes[concept_id].memories.append(memory.name)

    return node

def build_mindmap_from_memories(memories: List[Memory]) -> MindMap:
    """Build or update mind-map from memories."""
    mindmap = MindMap()

    # Group memories by concept (from tags or metadata)
    concept_groups = {}
    for mem in memories:
        concept = mem.metadata.get("concept")
        if not concept and mem.tags:
            # Use first tag as concept
            concept = mem.tags[0]
        if not concept:
            concept = "general"

        if concept not in concept_groups:
            concept_groups[concept] = []
        concept_groups[concept].append(mem)

    # Create concept nodes and link memories
    for concept, mems in concept_groups.items():
        concept_id = concept.lower().replace(" ", "-")
        add_concept(mindmap, concept_id, concept.title(), tags=[concept])

        for mem in mems:
            add_memory_node(mindmap, mem, concept_id)

    return mindmap

# ─── Token Estimation ────────────────────────────────────────────────────────

def estimate_tokens(config: Dict[str, Any],
                    exchanges: int = 0,
                    files_read: int = 0,
                    memories_loaded: int = 0,
                    lines_written: int = 0) -> Dict[str, int]:
    """Estimate current token usage."""
    est = config.get("estimation", {})

    base = est.get("base_overhead", 20000)
    conv = exchanges * est.get("tokens_per_exchange", 350)
    files = files_read * est.get("tokens_per_line", 20) * 200  # assume 200 lines/file
    mems = memories_loaded * est.get("tokens_per_memory", 200)
    written = lines_written * est.get("tokens_per_line", 20)

    total = int((base + conv + files + mems + written) * est.get("calibration_factor", 1.0))

    return {
        "base": base,
        "conversation": conv,
        "files": files,
        "memories": mems,
        "written": written,
        "total": total,
        "remaining": 200000 - total,
        "percent": round(total / 200000 * 100, 1)
    }

def format_budget(budget: Dict[str, int]) -> str:
    """Format budget as readable string."""
    lines = [
        "📊 Token Budget Estimate",
        "────────────────────────",
        f"Base overhead:           {budget['base']:,}",
        f"Conversation:            {budget['conversation']:,}",
        f"Files read:              {budget['files']:,}",
        f"Memories loaded:         {budget['memories']:,}",
        f"Code written:            {budget['written']:,}",
        "────────────────────────",
        f"Current:                 {budget['total']:,} ({budget['percent']}% of window)",
        f"Remaining:               {budget['remaining']:,}",
    ]

    if budget['percent'] >= 75:
        lines.append("⚠️  CRITICAL: Consider /clear or /token-optimizer prune")
    elif budget['percent'] >= 50:
        lines.append("⚡ WARNING: Context at 50%+")
    else:
        lines.append("✅ Healthy — continue")

    return "\n".join(lines)

# ─── Commands ────────────────────────────────────────────────────────────────

def cmd_load(args, config):
    """Load relevant memories for a topic."""
    topic = args.topic or ""
    memories = load_memories()

    # Score memories by relevance to topic
    scored = []
    topic_lower = topic.lower()
    topic_words = set(topic_lower.split())

    for mem in memories:
        score = 0
        text = f"{mem.name} {mem.description} {' '.join(mem.tags)}".lower()

        # Keyword matching
        for word in topic_words:
            if word in text:
                score += 2

        # Relevance bonus
        if mem.relevance == "high":
            score += 3
        elif mem.relevance == "medium":
            score += 1

        # Tag matching
        for tag in mem.tags:
            if tag in topic_lower:
                score += 2

        if score > 0 or not topic:
            scored.append((score, mem))

    scored.sort(key=lambda x: -x[0])
    top_memories = [m for _, m in scored[:config.get("memory_auto_load_max", 20)]]

    print(f"📚 Loaded {len(top_memories)} memories for topic: '{topic or 'all'}'")
    for mem in top_memories:
        print(f"  • {mem.name} — {mem.description}")

    return top_memories

def cmd_save(args, config):
    """Extract and save memories from current session."""
    print("💾 Session save triggered")
    print("   (In practice, this would analyze the session transcript)")
    print("   Use the skill's /token-optimizer save command in Claude Code")
    return []

def cmd_budget(args, config):
    """Show token budget estimate."""
    # These would come from session tracking in real usage
    budget = estimate_tokens(config,
        exchanges=args.exchanges or 10,
        files_read=args.files or 3,
        memories_loaded=args.memories or 5,
        lines_written=args.written or 100
    )
    print(format_budget(budget))
    return budget

def cmd_mindmap(args, config):
    """Show mind-map visualization."""
    mindmap = load_mindmap()

    if args.concept:
        # Show subgraph
        concept = mindmap.nodes.get(args.concept)
        if not concept:
            print(f"Concept '{args.concept}' not found")
            return

        print(f"🧠 Mind-map: {concept.label}")
        print("─" * 40)
        print(f"  {concept.label} ({concept.type})")
        for mem_id in concept.memories:
            mem = mindmap.nodes.get(mem_id)
            if mem:
                print(f"    ├── {mem.label} [{mem.relevance}]")
        for edge in mindmap.edges:
            if edge.from_id == args.concept:
                target = mindmap.nodes.get(edge.to_id)
                if target:
                    print(f"    └── {edge.type} → {target.label}")
    else:
        # Show all concepts
        print("🧠 Mind-map Overview")
        print("─" * 40)
        concepts = [n for n in mindmap.nodes.values() if n.type == "concept"]
        for c in concepts:
            mem_count = len(c.memories)
            print(f"  {c.label} ({mem_count} memories)")
            for mem_id in c.memories[:5]:
                mem = mindmap.nodes.get(mem_id)
                if mem:
                    print(f"    • {mem.label} [{mem.relevance}]")
            if mem_count > 5:
                print(f"    ... and {mem_count - 5} more")

def cmd_consolidate(args, config):
    """Consolidate duplicate/related memories."""
    memories = load_memories()
    mindmap = load_mindmap()

    print("🔍 Analyzing memories for consolidation...")

    # Find duplicates
    duplicates = []
    for i, mem_a in enumerate(memories):
        for mem_b in memories[i+1:]:
            # Simple similarity: tag overlap + name similarity
            tag_overlap = len(set(mem_a.tags) & set(mem_b.tags))
            name_sim = difflib.SequenceMatcher(None, mem_a.name, mem_b.name).ratio()

            if tag_overlap >= 2 and name_sim > 0.7:
                duplicates.append((mem_a, mem_b, name_sim))

    if duplicates:
        print(f"Found {len(duplicates)} potential duplicates:")
        for a, b, sim in duplicates:
            print(f"  • {a.name} ↔ {b.name} (similarity: {sim:.2f})")
            print(f"    Tags: {a.tags} / {b.tags}")
    else:
        print("No duplicates found.")

    # Check staleness
    stale = []
    for mem in memories:
        # In real implementation, check last_referenced
        pass

    if args.apply and duplicates:
        print("\n🔄 Applying consolidation...")
        # Would merge memories here
        print("   (Apply logic would merge and update mind-map)")

def cmd_stats(args, config):
    """Show memory/mind-map statistics."""
    memories = load_memories()
    mindmap = load_mindmap()

    print("📈 Token Optimizer Statistics")
    print("═" * 40)
    print(f"Memories:      {len(memories)}")
    print(f"Concepts:      {len([n for n in mindmap.nodes.values() if n.type == 'concept'])}")
    print(f"Total nodes:   {len(mindmap.nodes)}")
    print(f"Edges:         {len(mindmap.edges)}")
    print(f"Last updated:  {mindmap.updated}")

    # By type
    by_type = {}
    for mem in memories:
        by_type[mem.memory_type] = by_type.get(mem.memory_type, 0) + 1
    print("\nBy type:")
    for t, c in sorted(by_type.items()):
        print(f"  {t}: {c}")

    # By relevance
    by_rel = {}
    for mem in memories:
        by_rel[mem.relevance] = by_rel.get(mem.relevance, 0) + 1
    print("\nBy relevance:")
    for r in ["high", "medium", "low"]:
        print(f"  {r}: {by_rel.get(r, 0)}")

def cmd_prune(args, config):
    """Prune low-relevance context."""
    print("✂️  Pruning low-relevance memories...")
    print("   (Would remove memories below relevance threshold from active context)")
    print(f"   Threshold: {config.get('memory_relevance_threshold', 0.3)}")

def cmd_export(args, config):
    """Export memories for backup."""
    memories = load_memories()
    mindmap = load_mindmap()

    export = {
        "exported": datetime.now().isoformat(),
        "project": get_project_slug(),
        "memories": [],
        "mindmap": {
            "nodes": {k: asdict(v) for k, v in mindmap.nodes.items()},
            "edges": [asdict(e) for e in mindmap.edges]
        }
    }

    for mem in memories:
        export["memories"].append({
            "name": mem.name,
            "description": mem.description,
            "metadata": mem.metadata,
            "content": mem.content
        })

    output = Path(args.output) if args.output else Path(f"token-optimizer-export-{datetime.now():%Y%m%d-%H%M%S}.json")
    output.write_text(json.dumps(export, indent=2))
    print(f"✅ Exported {len(memories)} memories to {output}")

# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Token Optimizer CLI")
    parser.add_argument("--project", help="Project slug (default: auto-detect)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # load
    p_load = subparsers.add_parser("load", help="Load relevant memories for topic")
    p_load.add_argument("topic", nargs="?", help="Topic to load memories for")

    # save
    subparsers.add_parser("save", help="Save session memories")

    # budget
    p_budget = subparsers.add_parser("budget", help="Show token budget estimate")
    p_budget.add_argument("--exchanges", type=int, help="Number of exchanges")
    p_budget.add_argument("--files", type=int, help="Number of files read")
    p_budget.add_argument("--memories", type=int, help="Number of memories loaded")
    p_budget.add_argument("--written", type=int, help="Lines of code written")

    # mindmap
    p_mindmap = subparsers.add_parser("mindmap", help="Show mind-map")
    p_mindmap.add_argument("concept", nargs="?", help="Concept to focus on")

    # consolidate
    p_consolidate = subparsers.add_parser("consolidate", help="Consolidate memories")
    p_consolidate.add_argument("--apply", action="store_true", help="Apply changes")

    # stats
    subparsers.add_parser("stats", help="Show statistics")

    # prune
    subparsers.add_parser("prune", help="Prune low-relevance context")

    # export
    p_export = subparsers.add_parser("export", help="Export memories")
    p_export.add_argument("-o", "--output", help="Output file path")

    args = parser.parse_args()
    config = load_config()

    # Set project slug if provided
    if args.project:
        os.environ["TOKEN_OPTIMIZER_PROJECT"] = args.project

    # Dispatch
    commands = {
        "load": cmd_load,
        "save": cmd_save,
        "budget": cmd_budget,
        "mindmap": cmd_mindmap,
        "consolidate": cmd_consolidate,
        "stats": cmd_stats,
        "prune": cmd_prune,
        "export": cmd_export,
    }

    if args.command in commands:
        commands[args.command](args, config)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()