---
name: token-optimizer
description: Optimize token usage in Claude Code sessions through intelligent memory management, session summarization, mind-map construction, and context pruning. Use when user wants to reduce token costs, manage long conversations, or build persistent knowledge across sessions.
tools: Read, Write, Edit, Bash, Glob, Grep, Task
hooks:
  - session_end: auto_extract_memories
  - post_tool_use: track_session_activity
  - pre_tool_use: estimate_token_cost
---

# Token Optimizer

A skill for reducing token expenditure in Claude Code by managing context intelligently across sessions. It builds a persistent "mind map" of your project knowledge, summarizes sessions into structured memories, and prunes irrelevant context.

## Core Philosophy

**Tokens are expensive; knowledge is reusable.** Instead of re-reading files and re-explaining context every session, we:
1. **Extract** key facts/decisions from each session into structured memories
2. **Organize** them into a queryable mind-map (concept → file → decision graph)
3. **Retrieve** only relevant context for the current task
4. **Consolidate** duplicate/outdated memories periodically

---

## Workflow

### Phase 1: Session Start - Context Loading

When invoked at session start (or via `/token-optimizer load`):

```bash
# 1. Load relevant memories for current task
# 2. Build/update mind-map from memory files
# 3. Show token budget estimate for session
```

**Commands:**
- `/token-optimizer load [task-description]` — Load relevant memories for a task
- `/token-optimizer budget` — Show estimated token usage for planned work

### Phase 2: During Session - Active Optimization

**Automatic (background):**
- Track files read, code written, decisions made
- Flag high-token operations (large file reads, verbose outputs)
- Suggest `/clear` when context exceeds threshold

**Manual commands:**
- `/token-optimizer snapshot` — Save current context checkpoint
- `/token-optimizer prune` — Remove low-relevance context from current session
- `/token-optimizer focus <topic>` — Narrow context to specific topic

### Phase 3: Session End - Automatic Knowledge Extraction

**Runs automatically via `session_end` hook — no user action needed.**

When the session ends (or `/token-optimizer save` invoked):

1. **Analyze** session transcript + tool activity (files read/written, commands run)
2. **Extract** structured memories using pattern detection:
   - **Decisions**: "Let's use X", "Go with Y", "Chose Z over W"
   - **Facts**: "The issue is...", "Root cause:", "Note that...", "Important:"
   - **Gotchas**: "This breaks when...", "Watch out for...", "Gotcha:"
   - **Patterns**: "Always do X", "Never do Y", "The pattern is..."
   - **References**: Links to docs, PRs, issues, external resources
3. **Score** each memory by relevance (high/medium/low) and novelty
4. **Save** to `~/.claude/projects/<project>/memory/` with mind-map links
5. **Consolidate** duplicates/superseded memories (configurable)
6. **Output** brief summary (1-2 lines) — silent unless `verbose: true`

**Background Tracking (during session):**
- `post_tool_use` hook tracks: files read, code written, commands, decisions noted
- `pre_tool_use` estimates token cost of large operations
- Builds in-memory session log for end-of-session extraction

**User Control:**
- `/token-optimizer auto on|off` — Toggle automatic extraction
- `/token-optimizer review` — Review pending extracted memories before save
- `/token-optimizer config verbose=true` — Show extraction summary each session

---

## Memory Structure

Memories live in `~/.claude/projects/<project>/memory/` as markdown files:

```markdown
---
name: short-kebab-slug
description: one-line summary for recall relevance
metadata:
  type: fact | decision | pattern | gotcha | reference
  tags: [tag1, tag2]
  relevance: high | medium | low
  session: <session-id>
  timestamp: <iso8601>
---

## Fact/Decision/Pattern

<concise statement>

**Context:** <why this matters>
**Files:** <related file paths>
**Related:** [[other-memory-slug]]
```

**MEMORY.md** (index) format:
```
- [Title](file.md) — hook: one-line relevance hint
```

---

## Mind-Map Structure

A JSON graph at `~/.claude/projects/<project>/mindmap.json`:

```json
{
  "nodes": {
    "auth-system": {
      "type": "concept",
      "label": "Authentication System",
      "memories": ["jwt-implementation", "session-management"],
      "files": ["auth/login.py", "auth/middleware.py"]
    },
    "jwt-implementation": {
      "type": "memory",
      "label": "JWT Implementation Details",
      "concept": "auth-system"
    }
  },
  "edges": [
    { "from": "auth-system", "to": "jwt-implementation", "type": "contains" },
    { "from": "jwt-implementation", "to": "session-management", "type": "relates-to" }
  ]
}
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/token-optimizer load [topic]` | Load relevant memories for topic/task |
| `/token-optimizer save` | Extract memories from current session |
| `/token-optimizer budget` | Show token usage estimate |
| `/token-optimizer mindmap` | Visualize current mind-map |
| `/token-optimizer consolidate` | Merge duplicate/related memories |
| `/token-optimizer prune [threshold]` | Remove low-relevance memories |
| `/token-optimizer stats` | Show memory/mind-map statistics |
| `/token-optimizer export` | Export memories for backup/sharing |

---

## Token-Saving Techniques (Built-In)

### 1. Relevance-Based Context Loading
Instead of dumping all memories, score each by relevance to current task:
- **High**: Directly mentioned in task, recent decisions, active files
- **Medium**: Related concepts, patterns in same domain
- **Low**: Historical context, resolved issues

### 2. Hierarchical Summarization
- **Session level**: 200-token summary of what was done
- **Topic level**: 500-token summary per major area
- **Project level**: 1000-token architectural overview

### 3. File Reference Over Content
Store `file:line` references instead of code snippets. Read on demand.

### 4. Decision Log Over Conversation
Record *what was decided* not *what was said*. One decision = one memory.

### 5. Auto-Pruning Rules
- Memories untouched > 30 days & low relevance → archive
- Duplicate memories (similarity > 0.85) → merge
- Superseded decisions → mark deprecated, link to replacement

---

## Integration with Built-In Memory

This skill **enhances** (not replaces) Claude Code's native memory system:
- Uses same `~/.claude/projects/<project>/memory/` directory
- Reads/writes standard memory format
- Adds mind-map layer on top
- Respects `MEMORY.md` index

---

## Configuration

Create `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/token-optimizer/config.yaml`:

```yaml
# Token thresholds
session_token_warning: 100000    # Warn when session approaches this
session_token_limit: 150000      # Suggest /clear at this point
memory_relevance_threshold: 0.3  # Below this: don't auto-load

# Mind-map settings
max_nodes_display: 50            # Max nodes in mind-map view
edge_types: [contains, relates-to, depends-on, supersedes]

# Consolidation
consolidation_similarity: 0.85   # Merge memories above this similarity
archive_after_days: 30           # Archive untouched low-relevance memories
max_memories_per_concept: 20     # Cap per concept node

# Auto-save
auto_save_on_session_end: true
auto_save_interval_minutes: 30   # Periodic checkpoint
```

---

## References

- [references/extraction-patterns.md](references/extraction-patterns.md) — Patterns for extracting memories from sessions
- [references/mindmap-schema.md](references/mindmap-schema.md) — Mind-map JSON schema
- [references/consolidation-rules.md](references/consolidation-rules.md) — Rules for merging memories
- [references/token-estimation.md](references/token-estimation.md) — Token estimation heuristics

---

## Example Usage

```
User: /token-optimizer load "add payment integration"
# Loads memories tagged: payment, billing, stripe, paddle, webhooks

User: (works on payment feature for 45 min)

User: /token-optimizer save
# Extracts: "Chose Paddle as MoR", "Webhook endpoint at /api/billing/webhook",
#           "User.membership field for entitlements", "CS-A1 decision"
# Updates mind-map: payment → paddle-integration, webhook-handler, entitlements

User: /token-optimizer mindmap
# Shows graph centered on payment concept
```

---

## What This Skill Does NOT Do

- ❌ Compress conversation history in real-time (Claude handles summarization)
- ❌ Modify Claude's internal context management
- ❌ Guarantee token reduction (depends on usage patterns)
- ❌ Replace good context hygiene (still share only relevant files)

---

## Tips for Maximum Token Savings

1. **Start sessions with `/token-optimizer load`** — Load only what you need
2. **Use `/token-optimizer snapshot`** before large refactors — Easy rollback context
3. **Run `/token-optimizer consolidate` weekly** — Keep memory graph clean
4. **Tag memories consistently** — `payment`, `auth`, `ui`, `perf`, `security`
5. **Link memories** — Use `[[other-slug]]` for explicit connections
6. **Review mind-map monthly** — Spot gaps, outdated info, missing links