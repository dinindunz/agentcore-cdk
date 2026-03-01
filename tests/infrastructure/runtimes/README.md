# Runtime Infrastructure Tests

Automated infrastructure tests for AgentCore runtime invocation and performance.

## Quick Start

```bash
make test-runtimes         # Run all runtime tests
```

See **[Infrastructure Testing Guide](../../../docs/INFRASTRUCTURE_TESTING.md#runtime-infrastructure-tests)** for complete documentation.

## Test Files

- **`test_agent_invocation.py`** - Agent runtime end-to-end orchestration tests
- **`test_mcp_invocation.py`** - MCP runtime direct invocation tests
- **`test_performance.py`** - Basic response time measurements
- **`conftest.py`** - Shared fixtures (runtime ARNs, test-user)

## What These Tests Validate

**Agent Runtime:**
- ✅ Can invoke agent with prompts
- ✅ Agent uses tools correctly (calculations)
- ✅ Returns properly structured responses
- ✅ Handles sessionId and actorId correctly

**MCP Runtime:**
- ✅ Direct tool invocation works
- ✅ List tools returns available tools
- ✅ Calculator operations return correct results

**Performance (Informational):**
- ⏱️ Agent response time (< 30s)
- ⏱️ MCP runtime response time (< 5s)

## Prerequisites

- Deployed stack (`make deploy`)
- Valid AWS credentials
- `.env` file with `REGION_NAME`
- Secrets in Secrets Manager for auth

## Auto-Skipping

Tests automatically skip if:
- Stack not deployed (runtime ARNs not in SSM)
- AWS credentials invalid
- Secrets not found

## Performance Tests

Performance tests measure response times but are not strict performance benchmarks - they just ensure reasonable response times:

- Agent response time: < 30 seconds
- MCP runtime response time: < 5 seconds
