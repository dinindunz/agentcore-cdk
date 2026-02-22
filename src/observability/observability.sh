#!/bin/bash
set -e

# Create Phoenix project
# Usage: ./scripts/deploy_observability.sh [env]

ENV=${1:-dev}
STACK_NAME="ObservabilityStack-${ENV}"
PROJECT_NAME="agentcore-stack-${ENV}"
REGION="ap-southeast-2"

echo ""
echo "✨ Creating Phoenix project '${PROJECT_NAME}'..."
python ../observability/create_phoenix_project.py \
  --stack-name "${STACK_NAME}" \
  --project-name "${PROJECT_NAME}" \
  --region "${REGION}"

echo ""
echo "✅ Observability stack deployed and Phoenix project created successfully!"
