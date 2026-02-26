# ==============================================================================
# Integration Tests (Pytest)
# ==============================================================================

test:
	@echo "Running all tests..."
	@pytest tests/ -v

test-integration:
	@echo "Running all integration tests..."
	@pytest tests/integration/ -v -m integration

test-memory:
	@echo "Running memory integration tests..."
	@pytest tests/integration/memory/ -v

test-memory-quick:
	@echo "Running memory integration tests (excluding slow tests)..."
	@pytest tests/integration/memory/ -v -m "integration and not slow"
