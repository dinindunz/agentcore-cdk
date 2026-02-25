from collections.abc import Sequence

import aws_cdk as cdk
import jsii
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct, IConstruct


@jsii.implements(cdk.IAspect)
class DestroyLogGroups:
    """Delete service-managed log groups on stack deletion.

    AgentCore runtimes, ECR deployment, and AwsCustomResource Lambdas
    create log groups outside CloudFormation. This aspect walks the
    construct tree and sets removal_policy=DESTROY on every LogGroup
    so they are cleaned up when the stack is destroyed.
    """

    def visit(self, node: IConstruct) -> None:
        if isinstance(node, logs.LogGroup):
            node.apply_removal_policy(cdk.RemovalPolicy.DESTROY)


class LogGroupCleanup(Construct):
    """Lambda-backed custom resource that deletes orphaned log groups on stack deletion.

    Services like AgentCore runtimes, ECR deployment, and AwsCustomResource Lambdas
    create log groups outside CloudFormation. This construct provisions a Lambda
    that scans for log groups matching the given prefixes and deletes them when
    the stack is destroyed.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        log_group_prefixes: Sequence[str],
    ) -> None:
        super().__init__(scope, construct_id)

        stack = cdk.Stack.of(self)

        # Explicit LogGroup so CloudFormation deletes it on stack destruction
        # (prevents the cleanup Lambda's own log group from being orphaned)
        cleanup_log_group = logs.LogGroup(
            self,
            "Logs",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Handle CFN custom resource protocol directly — avoids the extra
        # framework Lambda that cr.Provider creates (another orphaned log group)
        self._function = lambda_.Function(
            self,
            "Fn",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            log_group=cleanup_log_group,
            code=lambda_.Code.from_inline(
                "import json, urllib.request, boto3\n"
                "def handler(event, context):\n"
                "    status, reason = 'SUCCESS', ''\n"
                "    pid = event.get('PhysicalResourceId', context.log_stream_name)\n"
                "    try:\n"
                "        if event['RequestType'] == 'Delete':\n"
                "            client = boto3.client('logs')\n"
                "            exclude = set(event['ResourceProperties'].get('Exclude', []))\n"
                "            for prefix in event['ResourceProperties']['Prefixes']:\n"
                "                paginator = client.get_paginator('describe_log_groups')\n"
                "                for page in paginator.paginate(logGroupNamePrefix=prefix):\n"
                "                    for lg in page['logGroups']:\n"
                "                        name = lg['logGroupName']\n"
                "                        if name not in exclude:\n"
                "                            client.delete_log_group(logGroupName=name)\n"
                "    except Exception as e:\n"
                "        print(e)\n"
                "        status, reason = 'FAILED', str(e)\n"
                "    body = json.dumps({'Status': status, 'Reason': reason or 'See CloudWatch',\n"
                "        'PhysicalResourceId': pid, 'StackId': event['StackId'],\n"
                "        'RequestId': event['RequestId'],\n"
                "        'LogicalResourceId': event['LogicalResourceId']}).encode()\n"
                "    req = urllib.request.Request(event['ResponseURL'], data=body, method='PUT')\n"
                "    req.add_header('Content-Type', '')\n"
                "    urllib.request.urlopen(req)\n"
            ),
            timeout=cdk.Duration.minutes(5),
        )
        self._function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:DescribeLogGroups"],
                resources=["*"],
            )
        )
        self._function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:DeleteLogGroup"],
                resources=[
                    f"arn:aws:logs:{stack.region}:{stack.account}:log-group:{prefix}*"
                    for prefix in log_group_prefixes
                ],
            )
        )
        self._function.add_permission(
            "CfnInvoke",
            principal=iam.ServicePrincipal("cloudformation.amazonaws.com"),
        )

        self._resource = cdk.CustomResource(
            self,
            "Resource",
            service_token=self._function.function_arn,
            properties={
                "Prefixes": list(log_group_prefixes),
                # Skip our own log group — it's CFN-managed via cleanup_log_group
                "Exclude": [cleanup_log_group.log_group_name],
            },
        )

    @property
    def resource(self) -> cdk.CustomResource:
        """The underlying custom resource, for setting up dependencies."""
        return self._resource
