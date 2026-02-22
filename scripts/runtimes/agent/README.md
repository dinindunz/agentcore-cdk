# Agent Runtime Scripts

Scripts for invoking the AgentCore agent runtime with Cognito JWT authentication.

## Overview

The agent runtime is an orchestration layer that coordinates multiple MCP servers/tools to handle complex, multi-step tasks. These scripts test agent capabilities using:
- **Authentication**: Cognito OAuth2 client_credentials flow
- **Endpoint**: `https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{runtime_arn}/invocations`

## Invocation Module

The `invoke_agent.py` module provides a reusable function for agent invocation:

### Functions

- **`invoke_agent(prompt: str)`** - Authenticate and invoke the agent with a prompt, printing the response

### Usage Example

```python
from invoke_agent import invoke_agent

invoke_agent("List my GitHub repositories and calculate total stars")
```

## Available Scripts

### Skill Tests
- **`skill_tests/issue_heat_map.py`** - Analyze repo issues/PRs, calculate maintenance burden index
- **`skill_tests/portfolio_summary.py`** - List user repos, calculate total/average stars
- **`skill_tests/repo_comparison.py`** - Compare multiple repositories
- **`skill_tests/repo_hotness_rating.py`** - Rate repository activity/popularity
- **`skill_tests/trending_topic_scout.py`** - Discover trending topics in repositories

## Configuration

Requires the following environment variables (via `.env`):
- `REGION_NAME` - AWS region (e.g., ap-southeast-2)

Requires the following AWS resources:
- SSM Parameter: `/agent-core-stack-dev/agent-runtime-arn`
- Secrets Manager Secret: `agent-core-stack-dev/agent-cognito` containing:
  - `client_id` - Cognito app client ID
  - `client_secret` - Cognito app client secret
  - `token_endpoint` - Cognito OAuth2 token endpoint

## How It Works

1. **Authenticate** - Get OAuth2 access token from Cognito using client_credentials grant
2. **Invoke Agent** - Send prompt to agent runtime with Bearer token
3. **Agent Orchestration** - Agent coordinates multiple tools/MCP servers to fulfill the request
4. **Stream Response** - Receive and display agent's response

## Adding New Skill Tests

To test new agent skills:

1. Create a new test file in `skill_tests/`
2. Import `invoke_agent` from the parent module
3. Call `invoke_agent()` with a prompt that exercises the desired skill
4. Update this README

Example:

```python
"""Skill: My New Skill — description of what it tests."""

from invoke_agent import invoke_agent

invoke_agent("Your prompt that tests the skill")
```
