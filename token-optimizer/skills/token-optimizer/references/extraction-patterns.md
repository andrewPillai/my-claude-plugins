# Memory Extraction Patterns

Patterns for extracting structured memories from Claude Code sessions.

---

## Pattern Categories

### 1. Decision Memories
**Trigger:** User makes a choice between options, approves a direction, or says "let's go with X"

**Template:**
```markdown
---
name: kebab-case-decision
description: One-line: what was decided
metadata:
  type: decision
  tags: [domain, feature]
  relevance: high
---

## Decision: <What was chosen>

**Alternatives considered:** <brief list>
**Rationale:** <why this choice>
**Impact:** <what this affects>
**Files:** <related files>
**Related:** [[other-memory]]
```

**Examples:**
- "Chose Paddle over Stripe for billing (MoR, global tax)"
- "Decided server-canonical verdicts; remove client engine at paid launch"
- "Selected React Query for server state management"

---

### 2. Fact Memories
**Trigger:** Discovering non-obvious information about the codebase, APIs, or constraints

**Template:**
```markdown
---
name: kebab-case-fact
description: One-line: the fact
metadata:
  type: fact
  tags: [domain]
  relevance: medium
---

## Fact: <The factual statement>

**Context:** <where/when this applies>
**Evidence:** <file:line, command output, doc reference>
**Caveats:** <exceptions, limitations>
**Related:** [[other-memory]]
```

**Examples:**
- "Tiingo free tier: 500 requests/day, EOD data only"
- "Render free tier spins down after 15 min inactivity"
- "User.membership is the single source of truth for entitlements"

---

### 3. Pattern Memories
**Trigger:** Recurring code patterns, conventions, or architectural approaches

**Template:**
```markdown
---
name: kebab-case-pattern
description: One-line: the pattern
metadata:
  type: pattern
  tags: [domain, layer]
  relevance: high
---

## Pattern: <Name of pattern>

**Where used:** <file paths or modules>
**Structure:** <code snippet or description>
**Variations:** <known variants>
**Anti-patterns:** <what to avoid>
**Related:** [[other-memory]]
```

**Examples:**
- "API errors route through market.data.public() — never expose provider details"
- "Signals exist in both static/js/app.js and market/signals.py — change both"
- "Run ./scripts/check.sh before pushing; includes parity tests"

---

### 4. Gotcha Memories
**Trigger:** Bugs, surprising behavior, things that caused wasted time

**Template:**
```markdown
---
name: kebab-case-gotcha
description: One-line: the gotcha
metadata:
  type: gotcha
  tags: [domain, severity]
  relevance: high
---

## Gotcha: <What trips people up>

**Symptoms:** <how it manifests>
**Root cause:** <why it happens>
**Fix/Workaround:** <what to do>
**Prevention:** <how to avoid in future>
**Files:** <where to look>
**Related:** [[other-memory]]
```

**Examples:**
- "git stash shared across worktrees — use WIP commits instead"
- "TradingView widget requires HTTPS; fails on localhost HTTP"
- "Parity tests compare JS/Python signals — must update both"

---

### 5. Reference Memories
**Trigger:** External resources, docs, tickets, PRs worth remembering

**Template:**
```markdown
---
name: kebab-case-ref
description: One-line: what this references
metadata:
  type: reference
  tags: [external, domain]
  relevance: low
---

## Reference: <Title>

**URL:** <link>
**Key info:** <what to extract>
**Expiry:** <when this becomes stale>
**Related:** [[other-memory]]
```

**Examples:**
- "Paddle webhook docs: https://developer.paddle.com/webhooks"
- "FTC Click-to-Cancel rule: https://www.ftc.gov/click-to-cancel"
- "PR #234: Added commodities support"

---

## Extraction Heuristics (For Automation)

### High-Confidence Triggers
| User/Assistant Action | Memory Type |
|----------------------|-------------|
| "Let's use X" / "Go with X" | decision |
| "The issue is..." / "Root cause:" | gotcha |
| "Always/never do X" | pattern |
| "Note: X" / "Important: X" | fact |
| Links to docs/PRs/issues | reference |

### Medium-Confidence Triggers
| Signal | Action |
|--------|--------|
| File read + "now I understand" | fact/pattern |
| Debugging session > 10 min | gotcha |
| Multiple file changes for one feature | decision + facts |
| "Why does X happen?" → answer | fact/gotcha |

### Low-Confidence (Require Confirmation)
- General preferences ("I prefer X")
- Tentative decisions ("Maybe we should...")
- Opinions without action

---

## Extraction Algorithm (Pseudo-code)

```python
def extract_memories(session_transcript, changed_files):
    memories = []
    
    # 1. Parse explicit markers
    for marker in ["DECISION:", "FACT:", "GOTCHA:", "PATTERN:", "REF:"]:
        memories.extend(parse_marked_sections(transcript, marker))
    
    # 2. Heuristic extraction from dialogue
    for exchange in transcript.exchanges:
        if is_decision_point(exchange):
            memories.append(extract_decision(exchange))
        if is_gotcha_discovery(exchange):
            memories.append(extract_gotcha(exchange))
        if is_pattern_recognition(exchange):
            memories.append(extract_pattern(exchange))
    
    # 3. From file changes
    for file in changed_files:
        memories.extend(extract_from_diff(file))
    
    # 4. Deduplicate & score
    memories = deduplicate(memories)
    memories = score_relevance(memories, session_context)
    
    return memories
```

---

## Quality Filters

**Keep if:**
- ✅ Specific to this project/codebase
- ✅ Non-obvious (not in docs/README)
- ✅ Actionable (affects future work)
- ✅ Verifiable (points to file/command)

**Discard if:**
- ❌ Generic best practice ("write tests")
- ❌ Obvious from code ("this function returns X")
- ❌ One-off/temporary ("today's debug session")
- ❌ Unverifiable opinion ("X is better")

---

## Tagging Taxonomy

**Domain tags:** `auth`, `billing`, `signals`, `charting`, `portfolio`, `alerts`, `data`, `ui`, `infra`, `testing`, `deploy`, `compliance`

**Layer tags:** `frontend`, `backend`, `database`, `api`, `worker`, `config`

**Priority tags:** `critical`, `high`, `medium`, `low`

**Status tags:** `active`, `deprecated`, `superseded`, `archived`

**Always use lowercase kebab-case. Max 5 tags per memory.**