# Agent Runtime Tests

Scripts for testing the AgentCore agent runtime with multi-tool orchestration.

## Quick Start

```bash
make agent-chat                # Interactive chat session
make skill-issue-heat-map      # Test issue heat map skill
make skill-portfolio-summary   # Test portfolio summary skill
```

See **[Manual Testing Guide](../../../../docs/MANUAL_TESTING.md#agent-runtime)** for complete documentation.

## Available Scripts

- **`chat_client.py`** - Interactive chat session with the agent
- **`invoke_agent.py`** - Reusable agent invocation module
- **`skill_tests/`** - Agent skill tests (issue heat map, portfolio summary, repo comparison, etc.)

## Adding New Skill Tests

1. Create new file in `skill_tests/`
2. Import `invoke_agent` from parent module
3. Call with prompt that exercises the skill
4. Update MANUAL_TESTING.md
