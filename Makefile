.PHONY: help

# Load environment variables from .env file (if it exists)
-include .env
export

# Environment variables
ENV ?= dev

# Default target - show help
help:
	@echo "AgentCore CDK - Make Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install                       - Set up virtual environment and install dependencies"
	@echo "  make setup-observability           - Enable CloudWatch Transaction Search (one-time account setup)"
	@echo ""
	@echo "CDK Deployment:"
	@echo "  make deploy                        - Deploy AgentCore stack (ENV=dev by default)"
	@echo "  make diff                          - Show AgentCore stack changes"
	@echo "  make destroy                       - Destroy AgentCore stack"
	@echo ""
	@echo "Skill Tests (Agent Runtime):"
	@echo "  make skill-issue-heat-map          - Test Issue Heat Map skill"
	@echo "  make skill-portfolio-summary       - Test Portfolio Summary skill"
	@echo "  make skill-repo-comparison         - Test Repo Comparison skill"
	@echo "  make skill-repo-hotness            - Test Repo Hotness Rating skill"
	@echo "  make skill-trending-topic          - Test Trending Topic Scout skill"
	@echo ""
	@echo "IAM Gateway - Tool Invocation:"
	@echo "  make iam-list-tools                - List all tools via IAM gateway"
	@echo "  make iam-search-tools              - Search tools via IAM gateway"
	@echo "  make iam-invoke-tool TOOL=<name> ARGS='<json>' - Invoke specific tool"
	@echo ""
	@echo "IAM Gateway - MCP Tests:"
	@echo "  make iam-test-calculator           - Test calculator via IAM gateway"
	@echo "  make iam-test-skill-search         - Test skill search via IAM gateway"
	@echo ""
	@echo "JWT Gateway - Tool Invocation:"
	@echo "  make jwt-list-tools                - List all tools via JWT gateway"
	@echo "  make jwt-search-tools              - Search tools via JWT gateway"
	@echo "  make jwt-invoke-tool TOOL=<name> ARGS='<json>' - Invoke specific tool"
	@echo ""
	@echo "JWT Gateway - MCP Tests:"
	@echo "  make jwt-test-github               - Test GitHub MCP via JWT gateway"
	@echo "  make jwt-test-temperature          - Test temperature converter via JWT gateway"
	@echo ""
	@echo "MCP Direct Runtime Invocation:"
	@echo "  make mcp-invoke-calculator         - Directly invoke calculator MCP runtime"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy ENV=prod               - Deploy AgentCore to production"
	@echo "  make diff ENV=test                 - Show changes for test environment"
	@echo "  make iam-invoke-tool TOOL=add ARGS='{\"a\": 5, \"b\": 3}'"
	@echo "  make jwt-invoke-tool TOOL=temperature-converter___celsius_to_fahrenheit ARGS='{\"celsius\": 25}'"

# ==============================================================================
# Setup Commands
# ==============================================================================

install:
	@echo "Setting up virtual environment and installing dependencies..."
	@PYTHON_CMD=""; \
	if command -v python >/dev/null 2>&1; then \
		python_version=$$(python --version 2>&1 | awk '{print $$2}'); \
		major=$$(echo $$python_version | cut -d. -f1); \
		minor=$$(echo $$python_version | cut -d. -f2); \
		if [ $$major -gt 3 ] || ([ $$major -eq 3 ] && [ $$minor -ge 12 ]); then \
			PYTHON_CMD="python"; \
		fi; \
	fi; \
	if [ -z "$$PYTHON_CMD" ] && command -v python3 >/dev/null 2>&1; then \
		python_version=$$(python3 --version 2>&1 | awk '{print $$2}'); \
		major=$$(echo $$python_version | cut -d. -f1); \
		minor=$$(echo $$python_version | cut -d. -f2); \
		if [ $$major -gt 3 ] || ([ $$major -eq 3 ] && [ $$minor -ge 12 ]); then \
			PYTHON_CMD="python3"; \
		fi; \
	fi; \
	if [ -z "$$PYTHON_CMD" ]; then \
		echo "✗ Error: Python 3.12 or higher is required"; \
		echo "  Please install Python 3.12+ and ensure it's available as 'python' or 'python3'"; \
		exit 1; \
	fi; \
	python_version=$$($$PYTHON_CMD --version 2>&1 | awk '{print $$2}'); \
	echo "✓ Python version $$python_version detected (using $$PYTHON_CMD)"; \
	if [ ! -d .venv ]; then \
		echo "Creating virtual environment..."; \
		$$PYTHON_CMD -m venv .venv; \
	else \
		echo "✓ Virtual environment already exists"; \
	fi; \
	echo "Installing dependencies into virtual environment..."; \
	.venv/bin/pip install --upgrade pip; \
	.venv/bin/pip install .
	@echo ""
	@echo "✓ Installation complete!"
	@echo ""
	@echo "Next step: Activate the virtual environment by running:"
	@echo "  source .venv/bin/activate"

setup-observability:
	@echo "Enabling CloudWatch Transaction Search for AgentCore observability..."
	@AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID) REGION_NAME=$(REGION_NAME) ./bin/setup-observability.sh

# ==============================================================================
# CDK Deployment Commands
# ==============================================================================

deploy:
	@echo "Deploying AgentCore stack (ENV=$(ENV))..."
	cdk deploy --context env=$(ENV) --require-approval never --exclusively AgentCoreStack-$(ENV)

diff:
	@echo "Showing changes for AgentCore stack (ENV=$(ENV))..."
	cdk diff --context env=$(ENV) --exclusively AgentCoreStack-$(ENV)

destroy:
	@echo "Destroying AgentCore stack (ENV=$(ENV))..."
	cdk destroy --context env=$(ENV) --exclusively AgentCoreStack-$(ENV)

# ==============================================================================
# Skill Tests (Agent Runtime)
# ==============================================================================

skill-issue-heat-map:
	@echo "Running Issue Heat Map skill test..."
	@cd scripts/runtimes/agent/skill_tests && python issue_heat_map.py

skill-portfolio-summary:
	@echo "Running Portfolio Summary skill test..."
	@cd scripts/runtimes/agent/skill_tests && python portfolio_summary.py

skill-repo-comparison:
	@echo "Running Repo Comparison skill test..."
	@cd scripts/runtimes/agent/skill_tests && python repo_comparison.py

skill-repo-hotness:
	@echo "Running Repo Hotness Rating skill test..."
	@cd scripts/runtimes/agent/skill_tests && python repo_hotness_rating.py

skill-trending-topic:
	@echo "Running Trending Topic Scout skill test..."
	@cd scripts/runtimes/agent/skill_tests && python trending_topic_scout.py

# Run all skill tests
skill-tests: skill-issue-heat-map skill-portfolio-summary skill-repo-comparison skill-repo-hotness skill-trending-topic

# ==============================================================================
# IAM Gateway - Tool Invocation
# ==============================================================================

iam-list-tools:
	@echo "Listing tools via IAM Gateway..."
	@cd scripts/gateways/iam && python list_tools.py

iam-search-tools:
	@echo "Searching tools via IAM Gateway..."
	@cd scripts/gateways/iam && python search_tools.py

iam-invoke-tool:
	@ifndef TOOL
		$(error TOOL is not set. Usage: make iam-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@ifndef ARGS
		$(error ARGS is not set. Usage: make iam-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@echo "Invoking tool $(TOOL) via IAM Gateway..."
	@cd scripts/gateways/iam && python invoke_tool.py $(TOOL) '$(ARGS)'

# ==============================================================================
# IAM Gateway - MCP Tests
# ==============================================================================

iam-test-calculator:
	@echo "Testing Calculator via IAM Gateway..."
	@cd scripts/gateways/iam/mcp_tests && python calculator.py

iam-test-skill-search:
	@echo "Testing Skill Search via IAM Gateway..."
	@cd scripts/gateways/iam/mcp_tests && python skill_search.py

# Run all IAM MCP tests
iam-mcp-tests: iam-test-calculator iam-test-skill-search

# ==============================================================================
# JWT Gateway - Tool Invocation
# ==============================================================================

jwt-list-tools:
	@echo "Listing tools via JWT Gateway..."
	@cd scripts/gateways/jwt && python list_tools.py

jwt-search-tools:
	@echo "Searching tools via JWT Gateway..."
	@cd scripts/gateways/jwt && python search_tools.py

jwt-invoke-tool:
	@ifndef TOOL
		$(error TOOL is not set. Usage: make jwt-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@ifndef ARGS
		$(error ARGS is not set. Usage: make jwt-invoke-tool TOOL=<tool_name> ARGS='<json>')
	@endif
	@echo "Invoking tool $(TOOL) via JWT Gateway..."
	@cd scripts/gateways/jwt && python invoke_tool.py $(TOOL) '$(ARGS)'

# ==============================================================================
# JWT Gateway - MCP Tests
# ==============================================================================

jwt-test-github:
	@echo "Testing GitHub MCP via JWT Gateway..."
	@cd scripts/gateways/jwt/mcp_tests && python github.py

jwt-test-temperature:
	@echo "Testing Temperature Converter via JWT Gateway..."
	@cd scripts/gateways/jwt/mcp_tests && python temperature_converter.py

# Run all JWT MCP tests
jwt-mcp-tests: jwt-test-github jwt-test-temperature

# ==============================================================================
# MCP Direct Runtime Invocation
# ==============================================================================

mcp-invoke-calculator:
	@echo "Directly invoking Calculator MCP runtime..."
	@cd scripts/runtimes/mcp && python invoke_calculator.py

# ==============================================================================
# Convenience Targets
# ==============================================================================

# Run all tests
all-tests: skill-tests iam-mcp-tests jwt-mcp-tests

# Run all IAM gateway tests
iam-tests: iam-list-tools iam-search-tools iam-mcp-tests

# Run all JWT gateway tests
jwt-tests: jwt-list-tools jwt-search-tools jwt-mcp-tests