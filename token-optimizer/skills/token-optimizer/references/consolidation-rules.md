# Memory Consolidation Rules

Rules for merging, archiving, and deprecating memories to keep the mind-map clean and relevant.

---

## Consolidation Triggers

Run consolidation when:
- `/token-optimizer consolidate` invoked manually
- Auto-save on session end (if enabled)
- Memory count > 200 for a project
- Weekly cron (if configured)

---

## Rule 1: Duplicate Detection

**Condition:** Two memories have semantic similarity > threshold (default 0.85)

**Detection methods:**
1. **Embedding similarity** (if available): cosine similarity of memory embeddings
2. **Keyword overlap**: Jaccard index of tag sets + title words > 0.7
3. **File overlap**: Same primary file references (> 80% overlap)
4. **Concept + type match**: Same concept node, same memory type

**Action:** Merge into single memory
```markdown
# Merged Memory
---
name: canonical-slug
description: Merged: <desc1> | <desc2>
metadata:
  type: <shared type>
  tags: <union of tags>
  relevance: <max of relevances>
  supersedes: [old-slug-1, old-slug-2]
---

## Original Memory 1
<content1>

## Original Memory 2
<content2>

**Merged on:** <date>
**Reason:** Duplicate detection (similarity: 0.92)
```

**Keep:** Most recent session, highest relevance, most tags

---

## Rule 2: Supersession Detection

**Condition:** New decision/fact explicitly contradicts or replaces old one

**Signals:**
- Memory contains "supersedes: [old-slug]" in metadata
- New decision says "instead of X, do Y"
- New fact says "X is no longer true; now Y"
- User explicitly says "that's outdated"

**Action:** 
1. Mark old memory `status: deprecated`
2. Add `superseded_by: new-slug` to old memory metadata
3. Add `supersedes: [old-slug]` to new memory metadata
4. Add edge `supersedes` in mind-map (new → old)

**Display:** Deprecated memories hidden by default; show with `--include-deprecated`

---

## Rule 3: Staleness Archival

**Condition:** Memory untouched for > threshold days (default 30) AND low relevance

**Untouched =** Not referenced in:
- Any session's loaded memories
- Any mind-map query result
- Any explicit user recall ("check the X memory")

**Thresholds by relevance:**
| Relevance | Archive After |
|-----------|---------------|
| high      | 90 days       |
| medium    | 60 days       |
| low       | 30 days       |

**Action:** Move to `memory/archive/` subdirectory; update mind-map node `status: archived`

**Recovery:** `/token-optimizer restore <slug>` moves back to active

---

## Rule 4: Concept Overcrowding

**Condition:** Concept node has > max_memories_per_concept (default 20) active memories

**Action:**
1. Sort memories by: relevance (high first) → recency → tag count
2. Keep top N; archive rest
3. Add summary memory: "Concept X has N archived memories (see archive/)"

---

## Rule 5: Orphan Cleanup

**Condition:** Memory node exists but:
- No mind-map edges connect it
- Not listed in any concept's `memories` array
- Not in MEMORY.md index

**Action:** 
- If has content → add to "unlinked" concept for review
- If empty/corrupt → delete with confirmation

---

## Rule 6: Circular Reference Resolution

**Condition:** Mind-map edges form cycle (A → B → C → A)

**Detection:** DFS cycle detection on mind-map graph

**Resolution:**
1. Identify weakest edge (lowest weight)
2. If `supersedes` edge in cycle → keep supersession, drop reverse
3. If `contains` cycle → flatten hierarchy (promote children to siblings)
4. Log resolution for user review

---

## Consolidation Algorithm

```python
def consolidate(mindmap, memories, config):
    actions = []
    
    # 1. Duplicate detection
    for mem_a, mem_b in pairwise(memories):
        sim = similarity(mem_a, mem_b)
        if sim > config.consolidation_similarity:
            actions.append(MergeAction(mem_a, mem_b, sim))
    
    # 2. Supersession (explicit metadata)
    for mem in memories:
        for old in mem.metadata.get('supersedes', []):
            actions.append(SupersedeAction(mem, old))
    
    # 3. Staleness
    for mem in memories:
        days_idle = (now - mem.last_referenced).days
        threshold = STALENESS_THRESHOLD[mem.metadata.relevance]
        if days_idle > threshold:
            actions.append(ArchiveAction(mem, f"idle {days_idle}d"))
    
    # 4. Overcrowding
    for concept in mindmap.concepts:
        active = [m for m in concept.memories if m.status == 'active']
        if len(active) > config.max_memories_per_concept:
            to_archive = sorted(active, key=sort_key)[config.max_memories_per_concept:]
            for m in to_archive:
                actions.append(ArchiveAction(m, "overcrowding"))
    
    # 5. Orphans
    for mem in memories:
        if is_orphan(mem, mindmap):
            actions.append(OrphanAction(mem))
    
    # 6. Cycles
    cycles = detect_cycles(mindmap)
    for cycle in cycles:
        actions.append(ResolveCycleAction(cycle))
    
    # Execute with confirmation
    return confirm_and_execute(actions)
```

---

## User Confirmation Flow

```
┌─────────────────────────────────────────────────────────┐
│  Consolidation Preview                                  │
├─────────────────────────────────────────────────────────┤
│  3 actions proposed:                                    │
│                                                         │
│  1. MERGE: "stripe-integration" + "paddle-integration" │
│     Similarity: 0.89 | Both: billing, decision         │
│     → Keep: "paddle-mor-decision" (newer, high rel)    │
│                                                         │
│  2. ARCHIVE: "old-webhook-format" (low, idle 45d)      │
│     Superseded by "webhook-v2-format"                  │
│                                                         │
│  3. DEPRECATE: "client-engine-approach"                │
│     Superseded by "server-canonical-verdicts" (CS-A5)  │
│                                                         │
│  [Apply All]  [Review Individually]  [Cancel]          │
└─────────────────────────────────────────────────────────┘
```

---

## Rollback

Every consolidation creates a backup:
- `mindmap.backup.json` — previous mind-map
- `memory/archive/YYYY-MM-DD-consolidation/` — archived memories

**Rollback command:** `/token-optimizer rollback [backup-date]`

---

## Configuration Reference

```yaml
consolidation:
  similarity_threshold: 0.85
  archive_after_days:
    high: 90
    medium: 60
    low: 30
  max_memories_per_concept: 20
  auto_consolidate_on_save: true
  require_confirmation: true
  backup_retention_days: 30
```