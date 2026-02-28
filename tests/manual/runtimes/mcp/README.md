# MCP Runtime Tests

Scripts for directly invoking MCP runtimes (containerised MCP servers on AgentCore).

## Quick Start

```bash
make mcp-invoke-calculator     # Test calculator runtime directly
```

See **[Manual Testing Guide](../../../../docs/MANUAL_TESTING.md#mcp-runtime)** for complete documentation.

## Available Scripts

- **`invoke_calculator.py`** - Test calculator MCP runtime (add tool)

## Adding New Runtime Tests

1. Deploy runtime to AgentCore
2. Use runtime ARN created in SSM
3. Create script following `invoke_calculator.py` pattern
4. Update MANUAL_TESTING.md
