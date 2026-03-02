# ==============================================================================
# Code Quality Commands
# ==============================================================================

lint:
	@echo "Linting Python code with ruff..."
	@.venv/bin/ruff check src/ tests/ scripts/ app.py

format:
	@echo "Formatting Python code with ruff..."
	@.venv/bin/ruff format src/ tests/ scripts/ app.py
	@.venv/bin/ruff check --select I --fix src/ tests/ scripts/ app.py
	@echo "✓ Code formatted successfully"
