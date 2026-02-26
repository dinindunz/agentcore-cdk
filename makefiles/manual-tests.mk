# ==============================================================================
# Manual Tests - Agent Runtime
# ==============================================================================

agent-hello:
	@echo "Sending hello to agent runtime..."
	@cd tests/manual/runtimes/agent && python hello.py

agent-chat:
	@echo "Starting interactive chat with agent..."
	@cd tests/manual/runtimes/agent && python chat_client.py

# ==============================================================================
# Manual Tests - Agent Skills
# ==============================================================================

skill-issue-heat-map:
	@echo "Running Issue Heat Map skill test..."
	@cd tests/manual/runtimes/agent/skill_tests && python issue_heat_map.py

skill-portfolio-summary:
	@echo "Running Portfolio Summary skill test..."
	@cd tests/manual/runtimes/agent/skill_tests && python portfolio_summary.py

skill-repo-comparison:
	@echo "Running Repo Comparison skill test..."
	@cd tests/manual/runtimes/agent/skill_tests && python repo_comparison.py

skill-repo-hotness:
	@echo "Running Repo Hotness Rating skill test..."
	@cd tests/manual/runtimes/agent/skill_tests && python repo_hotness_rating.py

skill-trending-topic:
	@echo "Running Trending Topic Scout skill test..."
	@cd tests/manual/runtimes/agent/skill_tests && python trending_topic_scout.py

# ==============================================================================
# Manual Tests - IAM Gateway
# ==============================================================================

iam-list-tools:
	@echo "Listing tools via IAM Gateway..."
	@cd tests/manual/gateways/iam && python list_tools.py

iam-search-tools:
	@echo "Searching tools via IAM Gateway..."
	@cd tests/manual/gateways/iam && python search_tools.py

iam-invoke-tool:
	@ifndef TOOL
		$(error TOOL is not set. Usage: make iam-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@ifndef ARGS
		$(error ARGS is not set. Usage: make iam-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@echo "Invoking tool $(TOOL) via IAM Gateway..."
	@cd tests/manual/gateways/iam && python invoke_tool.py $(TOOL) '$(ARGS)'

iam-test-calculator:
	@echo "Testing Calculator via IAM Gateway..."
	@cd tests/manual/gateways/iam/mcp_tests && python calculator.py

iam-test-skill-search:
	@echo "Testing Skill Search via IAM Gateway..."
	@cd tests/manual/gateways/iam/mcp_tests && python skill_search.py

iam-mcp-tests: iam-test-calculator iam-test-skill-search

# ==============================================================================
# Manual Tests - JWT Gateway
# ==============================================================================

jwt-list-tools:
	@echo "Listing tools via JWT Gateway..."
	@cd tests/manual/gateways/jwt && python list_tools.py

jwt-search-tools:
	@echo "Searching tools via JWT Gateway..."
	@cd tests/manual/gateways/jwt && python search_tools.py

jwt-invoke-tool:
	@ifndef TOOL
		$(error TOOL is not set. Usage: make jwt-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@ifndef ARGS
		$(error ARGS is not set. Usage: make jwt-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@echo "Invoking tool $(TOOL) via JWT Gateway..."
	@cd tests/manual/gateways/jwt && python invoke_tool.py $(TOOL) '$(ARGS)'

jwt-test-github:
	@echo "Testing GitHub MCP via JWT Gateway..."
	@cd tests/manual/gateways/jwt/mcp_tests && python github.py

jwt-test-temperature:
	@echo "Testing Temperature Converter via JWT Gateway..."
	@cd tests/manual/gateways/jwt/mcp_tests && python temperature_converter.py

jwt-mcp-tests: jwt-test-github jwt-test-temperature

# ==============================================================================
# Manual Tests - MCP Runtime
# ==============================================================================

mcp-invoke-calculator:
	@echo "Directly invoking Calculator MCP runtime..."
	@cd tests/manual/runtimes/mcp && python invoke_calculator.py

# ==============================================================================
# Manual Tests - Memory
# ==============================================================================

view-memory:
	@echo "Viewing AgentCore memory..."
	@python tests/manual/memory/view_memory.py

# ==============================================================================
# Manual Tests - Evaluations
# ==============================================================================

PYTHON := .venv/bin/python

eval-list:
	@echo "📊 Listing online evaluation configurations..."
	@$(PYTHON) tests/manual/evaluations/list_configs.py

eval-results:
	@echo "🔍 Querying evaluation results from CloudWatch Logs..."
	@$(PYTHON) tests/manual/evaluations/query_results.py $(if $(HOURS),$(HOURS),1)
