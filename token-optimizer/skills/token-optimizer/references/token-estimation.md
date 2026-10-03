# Token Estimation Heuristics

Practical token counting for Claude Code session planning and optimization.

---

## Token Basics

| Unit | Approximate Tokens |
|------|-------------------|
| 1 English word | 1.3 tokens |
| 1 code line (avg) | 15-25 tokens |
| 1 JSON object (small) | 50-100 tokens |
| 1 screen of code (50 lines) | ~1,000 tokens |
| 1 typical file (200 lines) | ~4,000 tokens |
| 1 conversation exchange | 200-500 tokens |

---

## Session Token Budget

### Context Window: ~200,000 tokens

**Typical allocation:**
| Component | Tokens | % |
|-----------|--------|---|
| System prompt + tools | ~15,000 | 7.5% |
| Conversation history | 50,000-100,000 | 25-50% |
| File contents read | 20,000-50,000 | 10-25% |
| Code written/output | 10,000-30,000 | 5-15% |
| **Available for task** | **~30,000-80,000** | **15-40%** |

---

## Estimation Formulas

### 1. File Read Cost
```
tokens = lines × 20 + overhead
overhead = 500 (file path, metadata, tool formatting)
```

**Examples:**
| File | Lines | Est. Tokens |
|------|-------|-------------|
| Small config | 30 | ~1,100 |
| Typical module | 200 | ~4,500 |
| Large component | 500 | ~10,500 |
| Minified bundle | 10,000 | ~200,500 ⚠️ |

### 2. Conversation History Cost
```
tokens = exchanges × 350 + summary_tokens
```
- Each user/assistant pair ≈ 350 tokens
- Summarized history: ~5,000 tokens per 100 exchanges

### 3. Memory Loading Cost
```
tokens = memories_loaded × 200 + mindmap_overhead
mindmap_overhead = 1,000 (graph structure)
```
- Typical memory: 150-300 tokens
- Loading 20 memories: ~5,000 tokens

### 4. Code Generation Cost
```
tokens = output_lines × 25 + context_tokens
context_tokens = relevant_memories + file_refs + instructions
```

---

## Budget Planning by Task Type

| Task Type | Typical Token Range | Optimization Strategy |
|-----------|---------------------|----------------------|
| Bug fix (localized) | 10,000-30,000 | Load only relevant memories; read 1-3 files |
| Feature implementation | 50,000-120,000 | Snapshot before; load domain memories; `/clear` mid-session |
| Refactoring (multi-file) | 80,000-180,000 | Split into sub-tasks; use snapshots; aggressive pruning |
| Code review | 30,000-80,000 | Load review-relevant memories; batch file reads |
| Exploration/learning | 20,000-60,000 | Focus mode; minimal memory loading |
| Debugging session | 40,000-150,000 | Snapshot at each hypothesis; prune dead ends |

---

## Warning Thresholds

```yaml
# Default thresholds (configurable)
token_warning: 100000      # Yellow: "Context at 50%"
token_critical: 150000     # Red: "Consider /clear or /token-optimizer prune"
token_limit: 180000        # Hard: Auto-summarize triggered
```

**At each threshold:**
- **Warning**: Show budget breakdown; suggest pruning
- **Critical**: Auto-suggest `/token-optimizer snapshot` + `/clear`
- **Limit**: Force summarize oldest 50% of conversation

---

## Token-Saving Tactics (Ranked by Impact)

### High Impact (≥30% savings)

| Tactic | How | Savings |
|--------|-----|---------|
| **Load selective memories** | `/token-optimizer load "topic"` vs all | 5,000-20,000 |
| **Use file refs not content** | "See `auth.py:45`" vs paste code | 2,000-10,000 per file |
| **Snapshot + clear** | Checkpoint → `/clear` → continue | 30,000-80,000 |
| **Batch file reads** | Read 5 files in one tool call | 2,000-5,000 (overhead) |

### Medium Impact (10-30% savings)

| Tactic | How | Savings |
|--------|-----|---------|
| **Summarize don't quote** | "Function does X" vs paste 50 lines | 1,000-5,000 |
| **Disable verbose tools** | `--quiet` flags, minimal output | 500-2,000 per call |
| **Reuse previous reads** | Reference earlier file content | 1,000-4,000 |
| **Focused mind-map queries** | Subgraph vs full graph | 500-2,000 |

### Low Impact (<10% savings)

| Tactic | How | Savings |
|--------|-----|---------|
| **Shorten prompts** | Concise instructions | 100-500 |
| **Avoid repetition** | Reference prior answers | 200-1,000 |
| **Use abbreviations** | "PR" vs "pull request" | 50-200 |

---

## Real-Time Estimation (During Session)

### Quick Mental Math
```
Current estimate = 
  (exchanges_so_far × 350) +
  (files_read × 4,000) +
  (memories_loaded × 200) +
  (code_written_lines × 25) +
  20,000 (base overhead)
```

### Tool-Assisted
```bash
# Built into skill: shows live estimate
/token-optimizer budget
```

**Output example:**
```
📊 Token Budget Estimate
────────────────────────
Base overhead:           20,000
Conversation (12 exch):  4,200
Files read (3):          12,000
Memories loaded (8):     1,600
Code written (150 lines): 3,750
────────────────────────
Current:                 41,550 (21% of window)
Remaining:               158,450

Projected (if continue 30 min): ~85,000
Recommendation: ✅ Healthy — continue
```

---

## Project-Specific Calibration

Track actual vs estimated for your project:

| Project | Avg file size | Avg exchange | Calibration factor |
|---------|---------------|--------------|-------------------|
| OnlineTrader | ~150 lines | ~400 tokens | 1.0x |
| Large monorepo | ~300 lines | ~500 tokens | 1.3x |
| Microservice | ~80 lines | ~300 tokens | 0.8x |

**Calibrate:** Run `/token-optimizer calibrate` after 5 sessions

---

## Emergency Procedures

### "Out of tokens" mid-task
1. `/token-optimizer snapshot` — Save progress context
2. `/clear` — Reset conversation
3. `/token-optimizer load <topic>` — Reload only essentials
4. Continue from snapshot

### "Context corrupted" (hallucinations, confusion)
1. `/token-optimizer save` — Extract what's valid
2. `/clear` — Full reset
3. `/token-optimizer load <topic>` — Fresh context
4. Verify key facts with `/token-optimizer mindmap`

---

## Monitoring Dashboard (Conceptual)

```
┌──────────────────────────────────────────────────────────┐
│  TOKEN USAGE DASHBOARD          Session: 47m             │
├──────────────────────────────────────────────────────────┤
│  ████████████████████░░░░░░░░░░░░░░░░  41,550 / 200,000  │
│                                                         │
│  📁 Files: 3 read (12k)    💾 Memories: 8 loaded (1.6k) │
│  💬 Exchanges: 12 (4.2k)   ✍️  Written: 150 lines (3.7k)│
│                                                         │
│  ⚡ Rate: 880 tokens/min    🎯 Projected: 85k total     │
│                                                         │
│  [Snapshot] [Prune] [Focus] [Mindmap] [Clear]          │
└──────────────────────────────────────────────────────────┘
```

---

## Integration with Claude Code

### Native Summarization
Claude Code auto-summarizes when context > ~180k tokens. This skill:
- **Complements** native summarization (structured vs narrative)
- **Preserves** decisions/facts that narrative summaries lose
- **Reduces** frequency of auto-summarization by keeping context lean

### Hook Points (Future)
- `pre_tool_use`: Estimate token cost of tool call
- `post_tool_use`: Track actual vs estimated
- `session_end`: Trigger auto-save/consolidation
- `context_warning`: Proactive pruning suggestions

---

## Quick Reference Card

```
┌────────────────────────────────────────┐
│  TOKEN QUICK REF                       │
├────────────────────────────────────────┤
│  1 file (200 lines)  ≈ 4,000 tok       │
│  1 exchange           ≈ 350 tok        │
│  1 memory             ≈ 200 tok        │
│  100 lines code       ≈ 2,500 tok      │
│                                        │
│  WARNING:  100k (50%)                  │
│  CRITICAL: 150k (75%)                  │
│  LIMIT:    180k (90%)                  │
│                                        │
│  SAVE:  /token-optimizer save          │
│  LOAD:  /token-optimizer load "topic"  │
│  CLEAR: /clear                         │
│  VIEW:  /token-optimizer budget        │
└────────────────────────────────────────┘
```