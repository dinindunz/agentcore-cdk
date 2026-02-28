# Gateway Infrastructure Tests

Automated infrastructure tests for AgentCore gateway authentication and tool invocation.

## Quick Start

```bash
make test-gateways         # Run all gateway tests
make test-gateways-quick   # Skip slow tests (faster development)
```

See **[Infrastructure Testing Guide](../../../docs/INFRASTRUCTURE_TESTING.md#gateway-infrastructure-tests)** for complete documentation.

## Test Files

- **`test_iam_auth.py`** - IAM gateway SigV4 authentication validation
- **`test_jwt_auth.py`** - JWT gateway OAuth2 token handling and refresh
- **`test_tool_invocation.py`** - End-to-end tool invocation (calculator, temperature converter)
- **`test_error_handling.py`** - Error scenarios (invalid tools, malformed arguments)
- **`conftest.py`** - Shared fixtures (gateway URLs, test-user)

## What These Tests Validate

**Authentication:**
- ✅ SigV4 signing works correctly (IAM gateway)
- ✅ OAuth2 token acquisition and caching (JWT gateway)
- ✅ Requests succeed with valid credentials

**Tool Invocation:**
- ✅ List tools returns expected structure
- ✅ Search tools finds relevant results
- ✅ Invoke tools returns correct responses
- ✅ Calculator addition works (IAM)
- ✅ Temperature conversion works (JWT)

**Error Handling:**
- ✅ Invalid tool names return errors
- ✅ Malformed arguments are rejected
- ✅ Invalid methods return appropriate errors

## Prerequisites

- Deployed stack (`make deploy`)
- Valid AWS credentials
- `.env` file with `REGION_NAME`

## Auto-Skipping

Tests automatically skip if:
- Stack not deployed (gateway URLs not in SSM)
- AWS credentials invalid
