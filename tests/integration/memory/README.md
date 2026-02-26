# Memory Integration Tests

Integration tests for AgentCore memory functionality.

## Quick Start

```bash
# Run all memory tests
make test-memory

# Skip slow tests (60-90s waits) - faster during development
make test-memory-quick

# Or using pytest directly
pytest tests/integration/memory/ -v

# Specific test file
pytest tests/integration/memory/test_memory_create.py -v
```

## Test Files

- **test_memory_create.py** - Create memory events (preferences, facts)
- **test_memory_queries.py** - Search and query memory records
- **test_memory_view.py** - List and view stored memories

## Key Fixtures

Shared fixtures in `conftest.py`:

- **`test_actor_id`** - Always returns `"test-user"` (for isolation)
- **`memory_id`** - Retrieved from SSM Parameter Store
- **`unique_session_id`** - UUID-based session ID (per test)
- **`bedrock_agentcore_client`** - Boto3 client for AgentCore

## Important Notes

### Memory Extraction Delay

Memory extraction is **asynchronous (60-90 seconds)**:

```bash
# Create test events
pytest tests/integration/memory/test_memory_create.py -v

# Wait for extraction
sleep 90

# Verify records exist
pytest tests/integration/memory/test_memory_view.py -v
```

### Test Isolation

- All tests use `test-user` as actor ID (never your real user)
- Unique session IDs prevent test interference
- Tests don't auto-cleanup (manual deletion via AWS console if needed)

### Auto-Skipping

Tests skip automatically if:
- Stack not deployed (memory ID not found in SSM)
- No records exist for test-user
- Prerequisites missing

## Troubleshooting

**"Memory ID not found"** → Run `make deploy`

**"No records found for test-user"** → Create test data:
```bash
pytest tests/integration/memory/test_memory_create.py -v
sleep 90
```