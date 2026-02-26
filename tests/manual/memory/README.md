# Memory Viewer

Quick utility to view AgentCore memory records.

## Usage

```bash
# View memory for actor from .env
make view-memory

# Specify custom actor ID
python tests/manual/memory/view_memory.py your-actor-id
```

## What It Shows

- **Preference memory** - User preferences and personalisation
- **Semantic memory** - Facts and knowledge about the user
- **Summary memory** - Session conversation summaries

## Example Output

```
================================================================================
AGENTCORE MEMORY VIEWER
================================================================================
Memory ID: mem-abc123...
Actor ID:  dini-123
================================================================================

📝 PREFERENCE MEMORY
Namespace: /preferences/dini-123/

  1. User prefers Australian English spelling
     Created: 2024-02-26T08:30:00Z

📝 SEMANTIC MEMORY
Namespace: /facts/dini-123/

  1. User lives in Melbourne, Australia
     Created: 2024-02-26T08:20:00Z
```