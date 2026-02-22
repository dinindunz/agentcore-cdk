# AgentCore CDK

## Project Structure

```
.
├── app.py                        # CDK application entry point
├── pyproject.toml                # Python project dependencies
├── Makefile                      # Build, deploy, and test commands
│
├── src/
│   ├── cdk/                      # CDK infrastructure code
│   │   ├── stacks/               # CloudFormation stacks
│   │   │   ├── agentcore.py      - Main AgentCore stack (gateways, runtimes, MCP servers)
│   │   │   └── observability.py  - Observability stack (Arize Phoenix, OpenTelemetry)
│   │   ├── constructs/           # Reusable L3 constructs
│   │   │   ├── cognito.py        - Cognito user pools and app clients
│   │   │   ├── gateway.py        - AgentCore gateways
│   │   │   ├── runtime.py        - AgentCore runtimes
│   │   │   ├── identity.py       - Credential providers (OAuth2, API keys)
│   │   │   ├── bucket.py         - S3 buckets with lifecycle policies (store skills)
│   │   │   └── gateway_targets/  - Gateway target configurations
│   │   │       ├── lambda_.py    - Lambda function targets
│   │   │       ├── mcp_server.py - MCP server targets
│   │   │       └── open_api.py   - OpenAPI targets
│   │   └── utils/                # Utility functions
│   │       ├── cleanup.py        - Log group cleanup aspects and custom resources
│   │       └── strings.py        - Case conversion utilities (kebab/PascalCase/snake_case)
│   │
│   ├── agent/                    # Agent runtime implementation
│   │   ├── main.py               - Agent entrypoint with Bedrock + MCP integration
│   │   ├── pyproject.toml        - Agent dependencies
│   │   └── Dockerfile            - Agent container image
│   │
│   ├── mcp/                      # MCP server implementations
│   │   ├── calculator/           - Basic calculator MCP server (MCP Server Target)
│   │   │   ├── main.py           - FastMCP server with arithmetic tools
│   │   │   ├── pyproject.toml    - Server dependencies (fastmcp)
│   │   │   └── Dockerfile        - Container image for Runtime deployment
│   │   ├── temperature_converter/ - Temperature conversion MCP server (Lambda Target)
│   │   │   ├── main.py           - FastMCP server with temp conversion tools
│   │   │   ├── schema.json       - Schema for Gateway integration
│   │   │   └── Dockerfile        - Container image for Runtime deployment
│   │   ├── skill_search/         - Skill search MCP server (Lambda Target)
│   │   │   ├── main.py           - FastMCP server with skill search tools
│   │   │   ├── schema.json       - Schema for Gateway integration
│   │   │   └── Dockerfile        - Container image for Runtime deployment
│   │   └── github/               - GitHub API MCP server (OpenAPI Target)
│   │       └── schema.json       - GitHub OpenAPI schema for Gateway target
│   │
│   ├── skills/                   # Agent skill definitions
│   │   ├── issue_heat_map.md
│   │   ├── portfolio_summary.md
│   │   ├── repo_comparison.md
│   │   ├── repo_hotness_rating.md
│   │   └── trending_topic_scout.md
│   │
│   └── observability/            # Observability setup utilities
│       └── create_phoenix_project.py
│
└── scripts/                      # Testing and invocation scripts
    ├── runtimes/
    │   ├── agent/                # Agent runtime testing
    │   │   ├── invoke_agent.py   - Invoke agent with SigV4 auth
    │   │   └── skill_tests/      - Test scripts for each agent skill
    │   └── mcp/                  # MCP runtime testing
    │       └── invoke_calculator.py
    └── gateways/
        ├── iam/                  # IAM-authenticated gateway testing
        │   ├── auth.py           - SigV4 signing helper
        │   ├── list_tools.py     - List available tools
        │   ├── search_tools.py   - Search tools by keyword
        │   ├── invoke_tool.py    - Invoke a specific tool
        │   └── mcp_tests/        - MCP protocol tests
        └── jwt/                  # JWT-authenticated gateway testing
            ├── auth.py           - Cognito authentication helper
            ├── list_tools.py
            ├── search_tools.py
            ├── invoke_tool.py
            └── mcp_tests/
```

## Usage

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

## Commands

All deployment, testing, and invocation commands are available through the Makefile:

```bash
# View all available commands
make help

# Deploy stacks
make deploy-observability      # Deploy Observability stack (ENV=dev by default)
make create-phoenix-project    # Create Phoenix project in Observability stack (run after deploying Observability stack)
make deploy-agentcore          # Deploy AgentCore (ENV=dev by default)
make deploy-all                # Deploy all stacks

# Run tests
make skill-tests               # Run all agent skill tests
make iam-tests                 # Run all IAM gateway tests
make jwt-tests                 # Run all JWT gateway tests
```

For the complete list of commands and detailed usage, run `make help` or see the **[Makefile](Makefile)**.

For infrastructure documentation, see **[CDK Infrastructure](src/cdk/README.md)**.
