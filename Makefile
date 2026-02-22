.PHONY: help

# Environment variable (default: dev)
ENV ?= dev
REGION ?= ap-southeast-2

# Default target - show help
help:
	@echo "AgentCore CDK - Make Commands"
	@echo "=============================="
	@echo ""
	@echo "CDK Deployment:"
	@echo "  make deploy-agentcore              - Deploy AgentCore stack (ENV=dev by default)"
	@echo "  make deploy-observability          - Deploy Observability stack (ENV=dev by default)"
	@echo "  make deploy-all                    - Deploy all stacks (ENV=dev by default)"
	@echo "  make diff-agentcore                - Show AgentCore stack changes"
	@echo "  make diff-observability            - Show Observability stack changes"
	@echo "  make diff-all                      - Show changes for all stacks"
	@echo "  make destroy-agentcore             - Destroy AgentCore stack"
	@echo "  make destroy-observability         - Destroy Observability stack"
	@echo "  make destroy-all                   - Destroy all stacks"
	@echo ""
	@echo "Observability:"
	@echo "  make create-phoenix-project        - Create Phoenix project"
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
	@echo "  make deploy-agentcore ENV=prod     - Deploy AgentCore to production"
	@echo "  make diff-agentcore ENV=test       - Show changes for test environment"
	@echo "  make create-phoenix-project ENV=prod REGION=us-west-2 PROJECT_NAME=my-project"
	@echo "  make iam-invoke-tool TOOL=add ARGS='{\"a\": 5, \"b\": 3}'"
	@echo "  make jwt-invoke-tool TOOL=temperature-converter___celsius_to_fahrenheit ARGS='{\"celsius\": 25}'"

# ==============================================================================
# CDK Deployment Commands
# ==============================================================================

deploy-agentcore:
	@echo "Deploying AgentCore stack (ENV=$(ENV))..."
	cdk deploy --context env=$(ENV) --require-approval never --exclusively AgentCoreStack-$(ENV)

deploy-observability:
	@echo "Deploying Observability stack (ENV=$(ENV))..."
	cdk deploy --context env=$(ENV) --require-approval never --exclusively ObservabilityStack-$(ENV)

deploy-all:
	@echo "Deploying all stacks in sequence (ENV=$(ENV))..."
	@$(MAKE) deploy-observability ENV=$(ENV)
	@$(MAKE) create-phoenix-project ENV=$(ENV) REGION=$(REGION)
	@$(MAKE) deploy-agentcore ENV=$(ENV)

diff-agentcore:
	@echo "Showing changes for AgentCore stack (ENV=$(ENV))..."
	cdk diff --context env=$(ENV) --exclusively AgentCoreStack-$(ENV)

diff-observability:
	@echo "Showing changes for Observability stack (ENV=$(ENV))..."
	cdk diff --context env=$(ENV) --exclusively ObservabilityStack-$(ENV)

diff-all:
	@echo "Showing changes for all stacks (ENV=$(ENV))..."
	cdk diff --context env=$(ENV) --all

destroy-agentcore:
	@echo "Destroying AgentCore stack (ENV=$(ENV))..."
	cdk destroy --context env=$(ENV) --exclusively AgentCoreStack-$(ENV)

destroy-observability:
	@echo "Destroying Observability stack (ENV=$(ENV))..."
	cdk destroy --context env=$(ENV) --exclusively ObservabilityStack-$(ENV)

destroy-all:
	@echo "Destroying all stacks (ENV=$(ENV))..."
	cdk destroy --context env=$(ENV) --all

# ==============================================================================
# Observability Commands
# ==============================================================================

create-phoenix-project:
	@echo "Creating Phoenix project agentcore-stack-$(ENV)..."
	python src/observability/create_phoenix_project.py \
		--stack-name ObservabilityStack-$(ENV) \
		--project-name agentcore-stack-$(ENV) \
		--region $(REGION)

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