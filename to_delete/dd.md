## Phoenix Project Creation

The ObservabilityStack deployment script (`./scripts/deploy/observability.sh`) automatically creates the Phoenix project after deployment.

If you deploy manually using `cdk deploy`, create the Phoenix project afterward:

```bash
# Create Phoenix project (default: agentcore-stack-dev)
python scripts/observability/create_phoenix_project.py

# Create with custom parameters
python scripts/observability/create_phoenix_project.py \
  --stack-name ObservabilityStack-prod \
  --project-name agentcore-stack-prod \
  --region ap-southeast-2
```

**Note**: Phoenix projects are created automatically when the agent sends its first trace. The script pre-creates the project namespace for organizational clarity, but it's optional.