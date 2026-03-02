# ==============================================================================
# Cognito User Management
# ==============================================================================

# Set PYTHONPATH to project root
PYTHON := PYTHONPATH=. .venv/bin/python

create-user:
ifndef ACTOR_ID
	$(error ACTOR_ID is not set in .env. Set it first: echo 'ACTOR_ID=your-name' >> .env)
endif
	@echo "Creating Cognito user: $(ACTOR_ID)..."
	@$(PYTHON) scripts/create_user.py $(ACTOR_ID)

list-users:
	@echo "Listing Cognito users..."
	@$(PYTHON) scripts/list_users.py
