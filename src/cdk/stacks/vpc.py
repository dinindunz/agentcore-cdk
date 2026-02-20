import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class AgentCoreVpcStack(cdk.Stack):
    """VPC with private subnets, NAT gateway, and AgentCore VPC endpoints."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------------------------------------------------------------
        # VPC — 2 AZs, public + private subnets, single NAT gateway
        # ---------------------------------------------------------------
        self._vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=1,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # ---------------------------------------------------------------
        # Security group for VPC interface endpoints
        # ---------------------------------------------------------------
        self._endpoint_sg = ec2.SecurityGroup(
            self,
            "EndpointSg",
            vpc=self._vpc,
            description="Allow HTTPS from within the VPC to interface endpoints",
            allow_all_outbound=False,
        )
        self._endpoint_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(self._vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="HTTPS from VPC CIDR",
        )

        # ---------------------------------------------------------------
        # Gateway endpoint — S3 (free, no interface charge)
        # ---------------------------------------------------------------
        self._vpc.add_gateway_endpoint(
            "S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # ---------------------------------------------------------------
        # Interface endpoints — AWS services accessed from private subnets
        # ---------------------------------------------------------------
        interface_services = {
            # ECR — pull container images
            "EcrApi": ec2.InterfaceVpcEndpointAwsService.ECR,
            "EcrDocker": ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            # CloudWatch — logs and metrics
            "CwLogs": ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            "CwMonitoring": ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_MONITORING,
            # Secrets Manager — credential injection
            "SecretsManager": ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            # SSM — parameter store
            "Ssm": ec2.InterfaceVpcEndpointAwsService.SSM,
            # STS — assume roles
            "Sts": ec2.InterfaceVpcEndpointAwsService.STS,
        }

        for endpoint_id, service in interface_services.items():
            self._vpc.add_interface_endpoint(
                endpoint_id,
                service=service,
                security_groups=[self._endpoint_sg],
                private_dns_enabled=True,
            )

        # ---------------------------------------------------------------
        # AgentCore VPC endpoints — Bedrock & AgentCore data/control planes
        # ---------------------------------------------------------------
        agentcore_services = {
            "BedrockRuntime": ec2.InterfaceVpcEndpointAwsService("bedrock-runtime"),
            "BedrockAgentCore": ec2.InterfaceVpcEndpointAwsService("bedrock-agentcore"),
            "BedrockAgentCoreRuntime": ec2.InterfaceVpcEndpointAwsService(
                "bedrock-agentcore-runtime"
            ),
        }

        for endpoint_id, service in agentcore_services.items():
            self._vpc.add_interface_endpoint(
                endpoint_id,
                service=service,
                security_groups=[self._endpoint_sg],
                private_dns_enabled=True,
            )

        # ---------------------------------------------------------------
        # Outputs
        # ---------------------------------------------------------------
        cdk.CfnOutput(self, "VpcId", value=self._vpc.vpc_id)
        cdk.CfnOutput(
            self,
            "PrivateSubnetIds",
            value=",".join([s.subnet_id for s in self._vpc.private_subnets]),
        )
        cdk.CfnOutput(
            self,
            "PublicSubnetIds",
            value=",".join([s.subnet_id for s in self._vpc.public_subnets]),
        )

    @property
    def vpc(self) -> ec2.Vpc:
        return self._vpc

    @property
    def endpoint_security_group(self) -> ec2.SecurityGroup:
        """Security group attached to all VPC interface endpoints."""
        return self._endpoint_sg
