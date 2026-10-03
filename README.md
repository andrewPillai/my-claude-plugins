# My Claude Code Plugins

Custom plugins for [Claude Code](https://claude.com/claude-code) — the AI-powered coding assistant.

## 📦 Plugins

### token-optimizer
**Token optimization skill for Claude Code** — Reduce token costs by 30-60% through intelligent context management.

**Features:**
- 🧠 **Automatic memory extraction** — Session-end hook extracts decisions, facts, gotchas, patterns without manual "remember this"
- 🗺️ **Mind-map knowledge graph** — Concept → Memory → File relationships with relevance scoring
- 📊 **Token budget tracking** — Real-time estimates with warning thresholds (50%/75%/90%)
- 🎯 **Relevance-based loading** — Load only memories relevant to current task (`/token-optimizer load "topic"`)
- 🔄 **Auto-consolidation** — Merge duplicates, archive stale, deprecate superseded memories
- 📁 **Native integration** — Uses `~/.claude/projects/*/memory/` format, enhances (not replaces) built-in memory

**Installation:**
```bash
# Clone this repo
git clone https://github.com/andrewPillai/my-claude-plugins.git

# Symlink to Claude plugins directory
ln -sf $(pwd)/token-optimizer ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/token-optimizer
```

**Usage:**
```bash
/token-optimizer load "billing integration"   # Load topic-relevant memories
/token-optimizer budget                       # Check token usage
/token-optimizer mindmap                      # View concept graph
/token-optimizer mindmap billing              # Focus on billing concept
/token-optimizer stats                        # Memory statistics
/token-optimizer consolidate                  # Find/merge duplicates
/token-optimizer consolidate --apply          # Actually apply merges
/token-optimizer export -o backup.json        # Backup everything
/token-optimizer auto off                     # Disable auto-extraction
```

**Configuration** (`config.yaml`):
```yaml
session_token_warning: 100000      # 50% warning
session_token_critical: 150000     # 75% critical
session_token_limit: 180000        # 90% hard limit
consolidation_similarity: 0.85     # Merge threshold
archive_after_days:                # Auto-archive stale memories
  high: 90
  medium: 60
  low: 30
```

---

## 🚀 Adding More Plugins

```bash
# Add a new plugin
mkdir -p my-claude-plugins/new-plugin-name
# ... add plugin files ...
git add new-plugin-name
git commit -m "Add new-plugin-name"
git push
```

## 📄 License

MIT — Use freely in your projects.
