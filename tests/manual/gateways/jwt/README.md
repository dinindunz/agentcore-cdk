# JWT Gateway Tests

Scripts for testing JWT-authenticated AgentCore gateway using Cognito OAuth2.

## Quick Start

```bash
make jwt-list-tools            # List all tools
make jwt-test-github           # Test GitHub MCP
make jwt-test-temperature      # Test temperature converter MCP
```

See **[Manual Testing Guide](../../../../docs/MANUAL_TESTING.md#jwt-gateway-cognito-oauth2)** for complete documentation.

## Available Scripts

- **`list_tools.py`** - List all available tools
- **`search_tools.py`** - Semantic tool search
- **`invoke_tool.py`** - Generic tool invocation
- **`mcp_tests/`** - Comprehensive MCP server tests (GitHub, Temperature Converter)

**Note:** Authentication logic is in `tests/common/auth/jwt.py` (shared with infrastructure tests)
