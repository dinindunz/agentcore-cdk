# IAM Gateway Tests

Scripts for testing IAM-authenticated AgentCore gateway using AWS SigV4.

## Quick Start

```bash
make iam-list-tools            # List all tools
make iam-test-calculator       # Test calculator MCP
make iam-test-skill-search     # Test skill search MCP
```

See **[Manual Testing Guide](../../../../docs/MANUAL_TESTING.md#iam-gateway-sigv4-auth)** for complete documentation.

## Available Scripts

- **`list_tools.py`** - List all available tools
- **`search_tools.py`** - Semantic tool search
- **`invoke_tool.py`** - Generic tool invocation
- **`mcp_tests/`** - Comprehensive MCP server tests (Calculator, Skill Search)

**Note:** Authentication logic is in `tests/common/auth/iam.py` (shared with infrastructure tests)
