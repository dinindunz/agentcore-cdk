# Memory Infrastructure Tests

Automated infrastructure tests for AgentCore memory functionality.

## Quick Start

```bash
make test-memory           # Run all memory tests
```

See **[Infrastructure Testing Guide](../../../docs/INFRASTRUCTURE_TESTING.md#memory-infrastructure-tests)** for complete documentation.

## Test Files

- **`test_memory_create.py`** - Create memory events (preferences, facts, summaries)
- **`test_memory_queries.py`** - Search and query memory records
- **`test_memory_view.py`** - List and view stored memories
- **`conftest.py`** - Shared fixtures (test_actor_id, memory_id, etc.)

## Important: Memory Extraction Delay

Memory extraction is **asynchronous (60-90 seconds)**. Wait after creating events before verifying:

```bash
pytest test_memory_create.py -v && sleep 90 && pytest test_memory_view.py -v
```

## Viewing Memory Records

To inspect memory records created by tests:

```bash
# View memory for test-user
make view-memory

# Specify custom actor ID
python tests/manual/memory/view_memory.py test-user
```

### What It Shows

- **Preference memory** - User preferences and personalisation
- **Semantic memory** - Facts and knowledge about the user
- **Summary memory** - Session conversation summaries
