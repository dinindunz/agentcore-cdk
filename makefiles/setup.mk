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
	@AWS_ACCOUNT_ID=$(AWS_ACCOUNT_ID) REGION_NAME=$(REGION_NAME) ./src/observability/setup.sh
