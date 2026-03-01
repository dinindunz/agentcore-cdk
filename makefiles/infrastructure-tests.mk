# ==============================================================================
# Infrastructure Tests (Pytest)
# ==============================================================================

test:
	@echo "Running all tests..."
	@pytest tests/ -v

test-infrastructure:
	@echo "Running all infrastructure tests..."
	@pytest tests/infrastructure/ -v -m infrastructure

# Gateway infrastructure tests
test-gateways:
	@echo "Running gateway infrastructure tests..."
	@pytest tests/infrastructure/gateways/ -v

# Runtime infrastructure tests
test-runtimes:
	@echo "Running runtime infrastructure tests..."
	@pytest tests/infrastructure/runtimes/ -v

# Memory infrastructure tests
test-memory:
	@echo "Running memory infrastructure tests..."
	@pytest tests/infrastructure/memory/ -v
