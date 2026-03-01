# ==============================================================================
# Observability Dashboard
# ==============================================================================

observability-frontend-install:
	@echo "📥 Installing frontend dependencies..."
	@cd src/observability/frontend && npm install

observability-frontend-build:
	@echo "📦 Building frontend for production..."
	@cd src/observability/frontend && npm run build

observability-dashboard:
	@echo "🔍 Launching AgentCore Observability Dashboard..."
	@$(PYTHON) src/observability/run.py

observability-frontend-dev:
	@echo "⚛️  Starting frontend development server..."
	@cd src/observability/frontend && npm run dev
