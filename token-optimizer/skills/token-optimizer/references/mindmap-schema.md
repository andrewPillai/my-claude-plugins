# Mind-Map Schema

JSON schema for the project mind-map at `~/.claude/projects/<project>/mindmap.json`.

---

## Schema (JSON Schema Draft 07)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "nodes", "edges", "updated"],
  "properties": {
    "version": { "type": "integer", "const": 1 },
    "nodes": {
      "type": "object",
      "patternProperties": {
        "^[a-z0-9-]+$": { "$ref": "#/$defs/node" }
      },
      "additionalProperties": false
    },
    "edges": {
      "type": "array",
      "items": { "$ref": "#/$defs/edge" }
    },
    "updated": { "type": "string", "format": "date-time" }
  },
  "$defs": {
    "node": {
      "type": "object",
      "required": ["id", "type", "label"],
      "properties": {
        "id": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "type": { "type": "string", "enum": ["concept", "memory", "file", "task", "external"] },
        "label": { "type": "string", "maxLength": 80 },
        "description": { "type": "string", "maxLength": 500 },
        "tags": { "type": "array", "items": { "type": "string" }, "maxItems": 10 },
        "memories": { "type": "array", "items": { "type": "string" } },
        "files": { "type": "array", "items": { "type": "string" } },
        "relevance": { "type": "string", "enum": ["high", "medium", "low"] },
        "status": { "type": "string", "enum": ["active", "deprecated", "archived"] },
        "session": { "type": "string" },
        "created": { "type": "string", "format": "date-time" },
        "updated": { "type": "string", "format": "date-time" }
      }
    },
    "edge": {
      "type": "object",
      "required": ["from", "to", "type"],
      "properties": {
        "from": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "to": { "type": "string", "pattern": "^[a-z0-9-]+$" },
        "type": { "type": "string", "enum": ["contains", "relates-to", "depends-on", "supersedes", "references", "implements", "documents"] },
        "weight": { "type": "number", "minimum": 0, "maximum": 1, "default": 1 },
        "note": { "type": "string", "maxLength": 200 }
      }
    }
  }
}
```

---

## Node Types

| Type | Purpose | Example |
|------|---------|---------|
| `concept` | High-level domain area | `auth-system`, `billing`, `signal-engine` |
| `memory` | Links to a memory file | `paddle-integration`, `jwt-gotcha` |
| `file` | Important source file | `auth-login-py`, `billing-webhook-py` |
| `task` | Ongoing/recurring work | `nightly-job`, `split-adjustment` |
| `external` | External resource | `paddle-docs`, `ftc-ruling` |

---

## Edge Types

| Type | Meaning | Direction |
|------|---------|-----------|
| `contains` | Parent concept contains child | concept → memory/file |
| `relates-to` | Semantic association | memory ↔ memory |
| `depends-on` | Dependency (build/order) | task → concept |
| `supersedes` | Replaces/deprecates | new-memory → old-memory |
| `references` | Cites external resource | memory → external |
| `implements` | Code implements concept | file → concept |
| `documents` | Memory documents file | memory → file |

---

## Example Mind-Map (OnlineTrader)

```json
{
  "version": 1,
  "nodes": {
    "billing": {
      "id": "billing",
      "type": "concept",
      "label": "Billing & Subscriptions",
      "description": "Paddle integration, entitlements, webhook handling",
      "tags": ["backend", "payments", "paid-tier"],
      "memories": ["paddle-mor-decision", "entitlements-sot", "webhook-endpoint"],
      "files": ["accounts/entitlements.py", "accounts/webhooks/paddle.py"],
      "relevance": "high",
      "status": "active",
      "session": "sess-20261003-001",
      "created": "2026-10-03T10:00:00Z",
      "updated": "2026-10-03T14:30:00Z"
    },
    "paddle-mor-decision": {
      "id": "paddle-mor-decision",
      "type": "memory",
      "label": "Paddle as Merchant of Record",
      "description": "Chose Paddle over Stripe for global tax handling",
      "tags": ["decision", "payments"],
      "concept": "billing",
      "relevance": "high",
      "status": "active",
      "session": "sess-20261002-005",
      "created": "2026-10-02T15:00:00Z",
      "updated": "2026-10-02T15:00:00Z"
    },
    "signal-engine": {
      "id": "signal-engine",
      "type": "concept",
      "label": "Signal Generation Engine",
      "description": "Dual implementation (JS/Python) with parity tests",
      "tags": ["core", "signals", "parity"],
      "memories": ["dual-implementation", "parity-tests", "server-canonical-decision"],
      "files": ["static/js/app/signals.js", "market/signals.py", "market/strategies.py"],
      "relevance": "high",
      "status": "active",
      "session": "sess-20260920-001",
      "created": "2026-09-20T09:00:00Z",
      "updated": "2026-10-03T11:00:00Z"
    },
    "server-canonical-decision": {
      "id": "server-canonical-decision",
      "type": "memory",
      "label": "Server-Canonical Verdicts (CS-A5)",
      "description": "Ship verdicts in /api/data; remove client engine at paid launch",
      "tags": ["decision", "architecture", "paid-launch-blocker"],
      "concept": "signal-engine",
      "relevance": "high",
      "status": "active",
      "session": "sess-20261001-003",
      "created": "2026-10-01T14:00:00Z",
      "updated": "2026-10-01T14:00:00Z"
    },
    "parity-tests": {
      "id": "parity-tests",
      "type": "memory",
      "label": "Parity Tests Compare JS/Python",
      "description": "scripts/js_coverage.py verifies no untested functions; signals must match",
      "tags": ["testing", "gotcha", "ci"],
      "concept": "signal-engine",
      "relevance": "high",
      "status": "active",
      "session": "sess-20260925-002",
      "created": "2026-09-25T10:00:00Z",
      "updated": "2026-09-25T10:00:00Z"
    }
  },
  "edges": [
    { "from": "billing", "to": "paddle-mor-decision", "type": "contains", "weight": 1.0 },
    { "from": "billing", "to": "entitlements-sot", "type": "contains", "weight": 1.0 },
    { "from": "signal-engine", "to": "server-canonical-decision", "type": "contains", "weight": 1.0 },
    { "from": "signal-engine", "to": "parity-tests", "type": "contains", "weight": 1.0 },
    { "from": "server-canonical-decision", "to": "dual-implementation", "type": "supersedes", "weight": 0.9, "note": "Client engine removal makes dual impl temporary" },
    { "from": "paddle-mor-decision", "to": "paddle-docs", "type": "references", "weight": 0.7 }
  ],
  "updated": "2026-10-03T14:30:00Z"
}
```

---

## Visualization Queries

### Subgraph for a Concept
```javascript
function getSubgraph(mindmap, conceptId, depth = 2) {
  const visited = new Set();
  const result = { nodes: {}, edges: [] };
  
  function traverse(nodeId, currentDepth) {
    if (currentDepth > depth || visited.has(nodeId)) return;
    visited.add(nodeId);
    
    if (mindmap.nodes[nodeId]) {
      result.nodes[nodeId] = mindmap.nodes[nodeId];
    }
    
    for (const edge of mindmap.edges) {
      if (edge.from === nodeId) {
        result.edges.push(edge);
        traverse(edge.to, currentDepth + 1);
      } else if (edge.to === nodeId) {
        result.edges.push(edge);
        traverse(edge.from, currentDepth + 1);
      }
    }
  }
  
  traverse(conceptId, 0);
  return result;
}
```

### Find Related Memories for Task
```javascript
function findRelevantMemories(mindmap, taskKeywords, maxResults = 10) {
  const scored = [];
  
  for (const [id, node] of Object.entries(mindmap.nodes)) {
    if (node.type !== 'memory') continue;
    
    let score = 0;
    const text = `${node.label} ${node.description} ${node.tags.join(' ')}`.toLowerCase();
    
    for (const kw of taskKeywords) {
      if (text.includes(kw.toLowerCase())) score += 1;
    }
    
    if (node.relevance === 'high') score += 2;
    else if (node.relevance === 'medium') score += 1;
    
    if (score > 0) scored.push({ id, node, score });
  }
  
  return scored
    .sort((a, b) => b.score - a.score)
    .slice(0, maxResults)
    .map(({ id, node }) => ({ id, ...node }));
}
```

---

## Maintenance Operations

### Add Node
```json
{
  "op": "add_node",
  "node": { ...node object... }
}
```

### Add Edge
```json
{
  "op": "add_edge",
  "edge": { "from": "concept-a", "to": "memory-b", "type": "contains" }
}
```

### Update Node
```json
{
  "op": "update_node",
  "id": "memory-b",
  "patch": { "relevance": "high", "updated": "2026-10-03T15:00:00Z" }
}
```

### Archive Node
```json
{
  "op": "archive_node",
  "id": "old-memory",
  "reason": "Superseded by new-memory"
}
```

---

## File Location

```
~/.claude/projects/<project-slug>/
├── memory/
│   ├── MEMORY.md              # Index
│   ├── paddle-mor-decision.md
│   └── ...
├── mindmap.json               # This schema
└── mindmap.backup.json        # Previous version (auto)
```

---

## Versioning

- **v1** (current): Basic concept/memory/file graph
- **v2** (planned): Temporal edges, session tracking, collaborative sync