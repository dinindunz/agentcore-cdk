#!/bin/bash
set -e

# Enable CloudWatch Transaction Search for AgentCore X-Ray tracing
# This is a one-time account-level setup required for AgentCore observability
# Script is idempotent - safe to run multiple times

AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
REGION_NAME="${REGION_NAME}"
POLICY_NAME="AgentCoreXRayAccess"

# Resolve AWS_ACCOUNT_ID from STS if not set
if [ -z "$AWS_ACCOUNT_ID" ]; then
  echo "⚠  AWS_ACCOUNT_ID not set — resolving from STS..."
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
  if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "❌ ERROR: Could not determine AWS account ID. Make sure you are authenticated (e.g. aws sso login)."
    exit 1
  fi
  echo "   Resolved account ID: $AWS_ACCOUNT_ID"
fi

if [ -z "$REGION_NAME" ]; then
  echo "❌ ERROR: REGION_NAME is not set. Export it or add it to your .env file."
  exit 1
fi

echo "🔍 Checking CloudWatch Transaction Search configuration..."
echo "   Region: $REGION_NAME"
echo "   Account: $AWS_ACCOUNT_ID"
echo ""

# Step 1: Check and create CloudWatch Logs resource policy for X-Ray
echo "📋 Step 1: CloudWatch Logs resource policy"
EXISTING_POLICY=$(aws logs describe-resource-policies \
  --region "$REGION_NAME" \
  --query "resourcePolicies[?policyName=='$POLICY_NAME'].policyName" \
  --output text 2>/dev/null || echo "")

if [ -n "$EXISTING_POLICY" ]; then
  echo "   ✓ Resource policy '$POLICY_NAME' already exists"
else
  echo "   → Creating resource policy '$POLICY_NAME'..."
  aws logs put-resource-policy \
    --region "$REGION_NAME" \
    --policy-name "$POLICY_NAME" \
    --policy-document "{
      \"Version\": \"2012-10-17\",
      \"Statement\": [{
        \"Sid\": \"TransactionSearchXRayAccess\",
        \"Effect\": \"Allow\",
        \"Principal\": {\"Service\": \"xray.amazonaws.com\"},
        \"Action\": \"logs:PutLogEvents\",
        \"Resource\": [
          \"arn:aws:logs:$REGION_NAME:$AWS_ACCOUNT_ID:log-group:aws/spans:*\",
          \"arn:aws:logs:$REGION_NAME:$AWS_ACCOUNT_ID:log-group:/aws/application-signals/data:*\"
        ]
      }]
    }" > /dev/null
  echo "   ✓ Resource policy created"
fi
echo ""

# Step 2: Check and set X-Ray trace segment destination
echo "🎯 Step 2: X-Ray trace segment destination"
CURRENT_DESTINATION=$(aws xray get-trace-segment-destination \
  --region "$REGION_NAME" \
  --query 'Destination' \
  --output text 2>/dev/null || echo "")

if [ "$CURRENT_DESTINATION" = "CloudWatchLogs" ]; then
  echo "   ✓ X-Ray destination already set to CloudWatchLogs"
else
  echo "   → Setting X-Ray destination to CloudWatchLogs (current: ${CURRENT_DESTINATION:-none})..."
  aws xray update-trace-segment-destination \
    --region "$REGION_NAME" \
    --destination CloudWatchLogs > /dev/null
  echo "   ✓ X-Ray destination updated"
fi
echo ""

# Step 3: Check and configure sampling rule (optional but recommended for testing)
echo "📊 Step 3: X-Ray sampling configuration"
CURRENT_SAMPLING=$(aws xray get-indexing-rules \
  --region "$REGION_NAME" \
  --query 'IndexingRules[?Name==`Default`].Rule.Probabilistic.DesiredSamplingPercentage' \
  --output text 2>/dev/null || echo "")

if [ "$CURRENT_SAMPLING" = "100" ]; then
  echo "   ✓ Sampling already set to 100%"
else
  echo "   → Setting sampling to 100% for testing (current: ${CURRENT_SAMPLING:-unknown}%)..."
  aws xray update-indexing-rule \
    --region "$REGION_NAME" \
    --name "Default" \
    --rule '{"Probabilistic": {"DesiredSamplingPercentage": 100}}' > /dev/null 2>&1 || {
    echo "   ⚠ Could not update sampling rule (may not exist yet - will be created on first trace)"
  }
  echo "   ✓ Sampling configuration updated"
fi
echo ""

echo "✅ CloudWatch Transaction Search setup complete!"
echo ""
echo "Next steps:"
echo "  1. Deploy your AgentCore stack with enable_observability=True"
echo "  2. Invoke your agent to generate traces"
echo "  3. View traces in:"
echo "     - AgentCore Console → Observability dashboard"
echo "     - X-Ray Console → Traces"
echo "     - CloudWatch Console → Application Signals → Transaction search"
