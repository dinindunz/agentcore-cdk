# Integration Tests

Integration tests for the AgentCore CDK project that interact with live AWS services.

## Structure

```
tests/integration/
├── README.md              # This file
└── memory/                # Memory-related integration tests
    ├── README.md          # Memory test documentation
    ├── conftest.py        # Memory test fixtures
    ├── test_memory_create.py
    ├── test_memory_queries.py
    └── test_memory_view.py
```

## Test Categories

### Memory Tests (`memory/`)

Integration tests for AgentCore memory strategies:
- Creating memory events (preferences, facts, summaries)
- Querying and searching memory records
- Viewing and listing stored memories

See [memory/README.md](memory/README.md) for details.

### Future Test Categories

As the project grows, add new subdirectories for:
- `gateway/` - Gateway and MCP proxy tests
- `runtime/` - Runtime and container hosting tests
- `evaluations/` - Evaluation and LLM-as-judge tests
- `auth/` - Cognito and authentication tests

## Running Tests

```bash
# All integration tests
make test-integration

# Memory tests
make test-memory
```

## Prerequisites

Follow setup steps in the [main README](../../README.md) up to `make deploy`.

## Best Practices

1. **Organise by Feature**: Group related tests in subdirectories
2. **Use Fixtures**: Share common setup via `conftest.py` files
3. **Mark Tests**: Use `@pytest.mark.integration` and `@pytest.mark.slow`
4. **Test Isolation**: Use unique IDs (e.g., `test-user`, unique session IDs)
5. **Document Prerequisites**: Clear requirements in README files
6. **Skip Gracefully**: Skip tests when prerequisites aren't met

## Markers

Configure in `pytest.ini`:
- `@pytest.mark.integration` - Requires AWS services
- `@pytest.mark.slow` - Long-running tests (> 60 seconds)