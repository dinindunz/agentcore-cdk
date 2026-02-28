# ==============================================================================
# Infrastructure Tests (Pytest)
# ==============================================================================

test:
	@echo "Running all tests..."
	@pytest tests/ -v

test-infrastructure:
	@echo "Running all infrastructure tests..."
	@pytest tests/infrastructure/ -v -m infrastructure

# Memory infrastructure tests
test-memory:
	@echo "Running memory infrastructure tests..."
	@pytest tests/infrastructure/memory/ -v

test-memory-quick:
	@echo "Running memory infrastructure tests (excluding slow tests)..."
	@pytest tests/infrastructure/memory/ -v -m "infrastructure and not slow"

# Gateway infrastructure tests
test-gateways:
	@echo "Running gateway infrastructure tests..."
	@pytest tests/infrastructure/gateways/ -v

test-gateways-quick:
	@echo "Running gateway infrastructure tests (excluding slow tests)..."
	@pytest tests/infrastructure/gateways/ -v -m "infrastructure and not slow"

# Runtime infrastructure tests
test-runtimes:
	@echo "Running runtime infrastructure tests..."
	@pytest tests/infrastructure/runtimes/ -v

test-runtimes-quick:
	@echo "Running runtime infrastructure tests (excluding slow tests)..."
	@pytest tests/infrastructure/runtimes/ -v -m "infrastructure and not slow"
