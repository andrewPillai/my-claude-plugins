# Feature Request: `session_start` Hook for Skills

## Summary
Add support for `session_start` hook in the Claude Code plugin/skill system to enable true automatic initialization of skills at the beginning of every session.

## Motivation
Currently, skills can only hook into:
- `session_end` — cleanup, save state
- `pre_tool_use` / `post_tool_use` — track activity during session
- `user_message` — respond to user input

**Missing:** `session_start` — initialize, auto-load context, show budget, restore state

## Use Case: Token Optimizer Skill
Our `token-optimizer` skill currently uses **lazy auto-load** (triggers on first command), but true `session_start` would enable:

```yaml
# In skill manifest (SKILL.md)
hooks:
  - session_start: auto_initialize
  - session_end: auto_extract_memories
  - pre_tool_use: estimate_token_cost
  - post_tool_use: track_session_activity
```

**Benefits:**
- Show token budget immediately on session start
- Auto-load relevant memories before first user command
- Restore session state (mind-map position, loaded memories)
- Display welcome summary: "Loaded 5 memories for 'billing' context. Budget: 42k tokens (21%)."

## Proposed API
```json
// hooks.json or SKILL.md frontmatter
{
  "hooks": {
    "session_start": "handler_function_name",
    "session_end": "handler_function_name",
    "pre_tool_use": "handler_function_name",
    "post_tool_use": "handler_function_name"
  }
}

// Handler receives:
{
  "session_id": "sess-20261003-001",
  "project_slug": "onlinetrader",
  "working_directory": "/Users/appi/OnlineTrader",
  "previous_session_id": "sess-20261002-005",
  "config": { ... }
}

// Handler returns:
{
  "auto_load_memories": ["mem1", "mem2"],
  "show_budget": true,
  "welcome_message": "Ready! 5 memories loaded."
}
```

## Priority
**High** — Enables truly invisible, automatic skills that "just work" without any user commands.

## Related
- Lazy auto-load workaround implemented in token-optimizer v0.2.0
- Would benefit all context-aware skills (memory, debugging, testing, etc.)
