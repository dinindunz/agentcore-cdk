# Deployment Troubleshooting

This document covers common issues you may encounter when deploying the AgentCore CDK stack and their solutions.

## Service-Linked Role Error

If deployment fails with:
```
Received response status [FAILED] from custom resource. Message returned: Error: An error occurred (ValidationException) when calling the CreateOnlineEvaluationConfig operation: The provided execution role does not have permissions to access the specified log groups Logs: /aws/lambda/AgentCoreStack-dev-AgentOnlineEvaluationHandlerCAF-hOO14BOXle8f at invokeUserFunction (/var/task/framework.js:2:6) at process.processTicksAndRejections (node:internal/process/task_queues:105:5) at async onEvent (/var/task/framework.js:1:369) at async Runtime.handler (/var/task/cfn-response.js:1:1837) (RequestId: 7495b647-60af-4c7f-abb0-158259dfbc33)
```
```
User is not authorized to perform: bedrock-agentcore:CreateOauth2CredentialProvider
on resource: arn:aws:bedrock-agentcore:ap-southeast-2:ACCOUNT_ID:token-vault/default/oauth2credentialprovider/*
```

### Solution

AWS usually auto-creates the required service-linked role (`AWSServiceRoleForBedrockAgentCoreRuntimeIdentity`) on first use. If it fails, simply **redeploy** and it should succeed on the second attempt.

The service-linked role is created automatically when you create or update an AgentCore Runtime (for runtimes created on or after October 13, 2025). Your IAM principal needs the `iam:CreateServiceLinkedRole` permission, which is included in the `BedrockAgentCoreFullAccess` managed policy.

## ResourceExistenceCheck Error (Orphaned Observability Resources)

If deployment fails with `AWS::EarlyValidation::ResourceExistenceCheck` for `AWS::Logs::DeliverySource` or `AWS::Logs::DeliveryDestination`, delete orphaned resources from a previous failed deployment:

### Solution

```bash
# List and identify orphaned resources
aws logs describe-delivery-sources --region REGION_NAME --query 'deliverySources[?name==`agent_core_stack_ENV_agent_traces`]'
aws logs describe-delivery-destinations --region REGION_NAME --query 'deliveryDestinations[?name==`agent_core_stack_ENV_agent_xray`]'

# Find the delivery ID
aws logs describe-deliveries --region REGION_NAME --query 'deliveries[?deliverySourceName==`agent_core_stack_ENV_agent_traces`]'

# Delete in order: delivery, source, destination
aws logs delete-delivery --id DELIVERY_ID --region REGION_NAME
aws logs delete-delivery-source --name agent_core_stack_ENV_agent_traces --region REGION_NAME
aws logs delete-delivery-destination --name agent_core_stack_ENV_agent_xray --region REGION_NAME
```

Replace `ENV` with your environment name (e.g., `dev`) and `REGION_NAME` with your AWS region.
