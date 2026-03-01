.PHONY: help

# Load environment variables from .env file (if it exists)
-include .env
export

# Environment variables
ENV ?= dev

# Include all sub-makefiles
include makefiles/setup.mk
include makefiles/config.mk
include makefiles/code-quality.mk
include makefiles/cdk.mk
include makefiles/infrastructure-tests.mk
include makefiles/manual-tests.mk
include makefiles/observability.mk
include makefiles/convenience.mk

# Default target - show help
help:
	@echo "AgentCore CDK - Make Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup:"
	@echo "  make install                       - Set up virtual environment and install dependencies"
	@echo "  make setup-observability           - Enable CloudWatch Transaction Search (one-time account setup)"
	@echo ""
	@echo "Configuration:"
	@echo "  make validate-config               - Validate all environment configurations (dev, test, prod)"
	@echo "  make validate-config ENV=dev       - Validate specific environment configuration"
	@echo "  make show-config ENV=dev           - Show current configuration for an environment"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                          - Lint Python code with ruff"
	@echo "  make format                        - Format Python code with ruff"
	@echo ""
	@echo "CDK Deployment:"
	@echo "  make deploy                        - Deploy AgentCore stack (ENV=dev by default)"
	@echo "  make diff                          - Show AgentCore stack changes"
	@echo "  make destroy                       - Destroy AgentCore stack"
	@echo ""
	@echo "Infrastructure Tests (Pytest):"
	@echo "  make test                          - Run all tests"
	@echo "  make test-infrastructure           - Run all infrastructure tests"
	@echo "  make test-memory                   - Run memory infrastructure tests"
	@echo "  make test-gateways                 - Run gateway infrastructure tests"
	@echo "  make test-runtimes                 - Run runtime infrastructure tests"
	@echo ""
	@echo "Manual Tests - Agent Runtime:"
	@echo "  make agent-hello                   - Send a hello message to the agent runtime"
	@echo "  make agent-chat                    - Start interactive chat with the agent"
	@echo ""
	@echo "Manual Tests - Agent Skills:"
	@echo "  make skill-issue-heat-map          - Test Issue Heat Map skill"
	@echo "  make skill-portfolio-summary       - Test Portfolio Summary skill"
	@echo "  make skill-repo-comparison         - Test Repo Comparison skill"
	@echo "  make skill-repo-hotness            - Test Repo Hotness Rating skill"
	@echo "  make skill-trending-topic          - Test Trending Topic Scout skill"
	@echo "  make skill-tests                   - Run all skill tests"
	@echo ""
	@echo "Manual Tests - IAM Gateway:"
	@echo "  make iam-list-tools                - List all tools via IAM gateway"
	@echo "  make iam-search-tools              - Search tools via IAM gateway"
	@echo "  make iam-invoke-tool TOOL=<name> ARGS='<json>' - Invoke specific tool"
	@echo "  make iam-test-calculator           - Test calculator via IAM gateway"
	@echo "  make iam-test-skill-search         - Test skill search via IAM gateway"
	@echo "  make iam-tests                     - Run all IAM gateway tests"
	@echo ""
	@echo "Manual Tests - JWT Gateway:"
	@echo "  make jwt-list-tools                - List all tools via JWT gateway"
	@echo "  make jwt-search-tools              - Search tools via JWT gateway"
	@echo "  make jwt-invoke-tool TOOL=<name> ARGS='<json>' - Invoke specific tool"
	@echo "  make jwt-test-github               - Test GitHub MCP via JWT gateway"
	@echo "  make jwt-test-temperature          - Test temperature converter via JWT gateway"
	@echo "  make jwt-tests                     - Run all JWT gateway tests"
	@echo ""
	@echo "Manual Tests - MCP Runtime:"
	@echo "  make mcp-invoke-calculator         - Directly invoke calculator MCP runtime"
	@echo ""
	@echo "Manual Tests - Memory:"
	@echo "  make view-memory                   - View stored memory records"
	@echo ""
	@echo "Manual Tests - Evaluations:"
	@echo "  make eval-list                     - List online evaluation configurations"
	@echo "  make eval-results                  - Query recent evaluation results (default: last 1 hour)"
	@echo "  make eval-results HOURS=<n>        - Query evaluation results for last N hours"
	@echo ""
	@echo "Observability Dashboard:"
	@echo "  make observability-frontend-install - Install frontend npm dependencies"
	@echo "  make observability-frontend-build  - Build frontend for production"
	@echo "  make observability-dashboard       - Launch observability web dashboard"
	@echo "  make observability-frontend-dev    - Start frontend dev server (port 3000)"
	@echo ""
	@echo "Convenience Targets:"
	@echo "  make all-tests                     - Run all tests (infrastructure + manual)"
	@echo "  make all-infrastructure-tests      - Run all pytest infrastructure tests"
	@echo "  make all-manual-tests              - Run all manual tests"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy ENV=prod               - Deploy AgentCore to production"
	@echo "  make diff ENV=test                 - Show changes for test environment"
	@echo "  make iam-invoke-tool TOOL=add ARGS='{\"a\": 5, \"b\": 3}'"
	@echo "  make jwt-invoke-tool TOOL=temperature-converter___celsius_to_fahrenheit ARGS='{\"celsius\": 25}'"
	@echo "  make eval-results HOURS=6          - Query evaluation results from last 6 hours"
