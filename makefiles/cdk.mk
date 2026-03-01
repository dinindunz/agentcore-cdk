# ==============================================================================
# CDK Deployment Commands
# ==============================================================================

deploy: format lint
	@echo "Deploying AgentCore stack (ENV=$(ENV))..."
	cdk deploy --context env=$(ENV) --require-approval never --exclusively AgentCoreStack-$(ENV)

diff: format lint
	@echo "Showing changes for AgentCore stack (ENV=$(ENV))..."
	cdk diff --context env=$(ENV) --exclusively AgentCoreStack-$(ENV)

destroy:
	@echo "Destroying AgentCore stack (ENV=$(ENV))..."
	cdk destroy --context env=$(ENV) --exclusively AgentCoreStack-$(ENV)
