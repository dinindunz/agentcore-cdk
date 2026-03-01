# ==============================================================================
# Manual Tests - Python Interpreter
# ==============================================================================

# Set PYTHONPATH to project root so tests can import from tests.common
PYTHON := PYTHONPATH=. .venv/bin/python

# ==============================================================================
# Manual Tests - Agent Runtime
# ==============================================================================

agent-hello:
	@echo "Sending hello to agent runtime..."
	@$(PYTHON) tests/manual/runtimes/agent/hello.py

agent-chat:
	@echo "Starting interactive chat with agent..."
	@$(PYTHON) tests/manual/runtimes/agent/chat_client.py

# ==============================================================================
# Manual Tests - Agent Skills
# ==============================================================================

skill-issue-heat-map:
	@echo "Running Issue Heat Map skill test..."
	@$(PYTHON) tests/manual/runtimes/agent/skill_tests/issue_heat_map.py

skill-portfolio-summary:
	@echo "Running Portfolio Summary skill test..."
	@$(PYTHON) tests/manual/runtimes/agent/skill_tests/portfolio_summary.py

skill-repo-comparison:
	@echo "Running Repo Comparison skill test..."
	@$(PYTHON) tests/manual/runtimes/agent/skill_tests/repo_comparison.py

skill-repo-hotness:
	@echo "Running Repo Hotness Rating skill test..."
	@$(PYTHON) tests/manual/runtimes/agent/skill_tests/repo_hotness_rating.py

skill-trending-topic:
	@echo "Running Trending Topic Scout skill test..."
	@$(PYTHON) tests/manual/runtimes/agent/skill_tests/trending_topic_scout.py

# ==============================================================================
# Manual Tests - IAM Gateway
# ==============================================================================

iam-list-tools:
	@echo "Listing tools via IAM Gateway..."
	@$(PYTHON) tests/manual/gateways/iam/list_tools.py

iam-search-tools:
	@echo "Searching tools via IAM Gateway..."
	@$(PYTHON) tests/manual/gateways/iam/search_tools.py

iam-invoke-tool:
ifndef TOOL
	$(error TOOL is not set. Usage: make iam-invoke-tool TOOL=<tool_name> ARGS='<json>')
endif
ifndef ARGS
	$(error ARGS is not set. Usage: make iam-invoke-tool TOOL=<tool_name> ARGS='<json>')
endif
	@echo "Invoking tool $(TOOL) via IAM Gateway..."
	@$(PYTHON) tests/manual/gateways/iam/invoke_tool.py $(TOOL) '$(ARGS)'

iam-test-calculator:
	@echo "Testing Calculator via IAM Gateway..."
	@$(PYTHON) tests/manual/gateways/iam/mcp_tests/calculator.py

iam-test-skill-search:
	@echo "Testing Skill Search via IAM Gateway..."
	@$(PYTHON) tests/manual/gateways/iam/mcp_tests/skill_search.py

iam-mcp-tests: iam-test-calculator iam-test-skill-search

# ==============================================================================
# Manual Tests - JWT Gateway
# ==============================================================================

jwt-list-tools:
	@echo "Listing tools via JWT Gateway..."
	@$(PYTHON) tests/manual/gateways/jwt/list_tools.py

jwt-search-tools:
	@echo "Searching tools via JWT Gateway..."
	@$(PYTHON) tests/manual/gateways/jwt/search_tools.py

jwt-invoke-tool:
ifndef TOOL
	$(error TOOL is not set. Usage: make jwt-invoke-tool TOOL=<tool_name> ARGS='<json>')
endif
ifndef ARGS
	$(error ARGS is not set. Usage: make jwt-invoke-tool TOOL=<tool_name> ARGS='<json>')
endif
	@echo "Invoking tool $(TOOL) via JWT Gateway..."
	@$(PYTHON) tests/manual/gateways/jwt/invoke_tool.py $(TOOL) '$(ARGS)'

jwt-test-github:
	@echo "Testing GitHub MCP via JWT Gateway..."
	@$(PYTHON) tests/manual/gateways/jwt/mcp_tests/github.py

jwt-test-temperature:
	@echo "Testing Temperature Converter via JWT Gateway..."
	@$(PYTHON) tests/manual/gateways/jwt/mcp_tests/temperature_converter.py

jwt-mcp-tests: jwt-test-github jwt-test-temperature

# ==============================================================================
# Manual Tests - MCP Runtime
# ==============================================================================

mcp-invoke-calculator:
	@echo "Directly invoking Calculator MCP runtime..."
	@$(PYTHON) tests/manual/runtimes/mcp/invoke_calculator.py

# ==============================================================================
# Manual Tests - Memory
# ==============================================================================

view-memory:
	@echo "Viewing AgentCore memory..."
	@$(PYTHON) tests/manual/memory/view_memory.py

# ==============================================================================
# Manual Tests - Evaluations
# ==============================================================================

eval-list:
	@echo "📊 Listing online evaluation configurations..."
	@$(PYTHON) tests/manual/evaluations/list_configs.py

eval-results:
	@echo "🔍 Querying evaluation results from CloudWatch Logs..."
	@$(PYTHON) tests/manual/evaluations/query_results.py $(if $(HOURS),$(HOURS),1)
