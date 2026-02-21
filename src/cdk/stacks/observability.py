import aws_cdk as cdk
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_logs as logs
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_iam as iam
from constructs import Construct

from ..utils import DestroyLogGroups, LogGroupCleanup, to_kebab_case


class ObservabilityStack(cdk.Stack):
    """Observability stack with Arize Phoenix and OpenTelemetry Collector."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stack_prefix = to_kebab_case(self.stack_name)
        cdk.Aspects.of(self).add(DestroyLogGroups())

        # ---------------------------------------------------------------
        # VPC — Single AZ, public subnet only (simplified for observability)
        # ---------------------------------------------------------------
        self._vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            nat_gateways=0,  # No NAT gateways needed for public-only setup
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
        )

        # ---------------------------------------------------------------
        # ECS Cluster for observability services
        # ---------------------------------------------------------------
        cluster = ecs.Cluster(
            self,
            "Cluster",
            cluster_name=stack_prefix,
            vpc=self._vpc,
            container_insights=True,  # Enable CloudWatch Container Insights
        )

        # ---------------------------------------------------------------
        # Phoenix API Key Secret
        # ---------------------------------------------------------------
        phoenix_api_key_secret = secretsmanager.Secret(
            self,
            "PhoenixApiKey",
            secret_name=f"{stack_prefix}/phoenix-api-key",
            description="API key for authenticating to Phoenix",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template="{}",
                generate_string_key="api_key",
                password_length=32,
            ),
        )

        # ---------------------------------------------------------------
        # Security Group for Phoenix service
        # ---------------------------------------------------------------
        phoenix_sg = ec2.SecurityGroup(
            self,
            "PhoenixSg",
            vpc=self._vpc,
            description="Security group for Arize Phoenix",
            allow_all_outbound=True,
        )

        # Allow inbound HTTP traffic on Phoenix port (6006)
        phoenix_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(6006),
            description="Phoenix HTTP",
        )

        # ---------------------------------------------------------------
        # Fargate Task Definition for Phoenix
        # ---------------------------------------------------------------
        phoenix_task_def = ecs.FargateTaskDefinition(
            self,
            "PhoenixTaskDef",
            family=f"{stack_prefix}-phoenix",
            cpu=512,
            memory_limit_mib=1024,
        )

        # Grant permission to read secrets
        phoenix_api_key_secret.grant_read(phoenix_task_def.task_role)

        # Phoenix container
        phoenix_container = phoenix_task_def.add_container(
            "Phoenix",
            image=ecs.ContainerImage.from_registry("arizephoenix/phoenix:latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="phoenix",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "PHOENIX_HOST": "0.0.0.0",
                "PHOENIX_PORT": "6006",
                "PHOENIX_WORKING_DIR": "/phoenix",
            },
            secrets={
                "PHOENIX_API_KEY": ecs.Secret.from_secrets_manager(
                    phoenix_api_key_secret, "api_key"
                ),
            },
        )

        phoenix_container.add_port_mappings(
            ecs.PortMapping(container_port=6006, protocol=ecs.Protocol.TCP)
        )

        # ---------------------------------------------------------------
        # Fargate Service for Phoenix
        # ---------------------------------------------------------------
        phoenix_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "PhoenixService",
            cluster=cluster,
            task_definition=phoenix_task_def,
            service_name=f"{stack_prefix}-phoenix",
            public_load_balancer=True,
            desired_count=1,
            assign_public_ip=True,
            security_groups=[phoenix_sg],
            listener_port=80,
            open_listener=True,
        )

        # Configure health check
        phoenix_service.target_group.configure_health_check(
            path="/healthz",
            port="6006",
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
            timeout=cdk.Duration.seconds(10),
            interval=cdk.Duration.seconds(30),
        )

        # ---------------------------------------------------------------
        # Security Group for OpenTelemetry Collector
        # ---------------------------------------------------------------
        otel_sg = ec2.SecurityGroup(
            self,
            "OtelSg",
            vpc=self._vpc,
            description="Security group for OpenTelemetry Collector",
            allow_all_outbound=True,
        )

        # Allow OTLP gRPC (4317) and HTTP (4318)
        otel_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(4317),
            description="OTLP gRPC",
        )
        otel_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(4318),
            description="OTLP HTTP",
        )
        otel_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(13133),
            description="OTel health check",
        )

        # ---------------------------------------------------------------
        # Fargate Task Definition for OpenTelemetry Collector
        # ---------------------------------------------------------------
        otel_task_def = ecs.FargateTaskDefinition(
            self,
            "OtelTaskDef",
            family=f"{stack_prefix}-otel-collector",
            cpu=256,
            memory_limit_mib=512,
        )

        # Grant necessary permissions
        otel_task_def.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:PutLogEvents",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                ],
                resources=["*"],
            )
        )

        # OpenTelemetry Collector container
        phoenix_endpoint = (
            f"http://{phoenix_service.load_balancer.load_balancer_dns_name}:80"
        )
        otel_config = (
            "receivers:\n"
            "  otlp:\n"
            "    protocols:\n"
            "      grpc:\n"
            "        endpoint: 0.0.0.0:4317\n"
            "      http:\n"
            "        endpoint: 0.0.0.0:4318\n"
            "exporters:\n"
            "  otlphttp:\n"
            f"    endpoint: {phoenix_endpoint}\n"
            "extensions:\n"
            "  health_check:\n"
            "    endpoint: 0.0.0.0:13133\n"
            "service:\n"
            "  extensions: [health_check]\n"
            "  pipelines:\n"
            "    traces:\n"
            "      receivers: [otlp]\n"
            "      exporters: [otlphttp]\n"
        )

        otel_container = otel_task_def.add_container(
            "OtelCollector",
            image=ecs.ContainerImage.from_registry(
                "otel/opentelemetry-collector-contrib:latest"
            ),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="otel-collector",
                log_retention=logs.RetentionDays.ONE_WEEK,
            ),
            environment={
                "OTEL_CONFIG": otel_config,
            },
            command=[
                "--config=env:OTEL_CONFIG",
            ],
        )

        # Add port mappings for OTLP and health check
        otel_container.add_port_mappings(
            ecs.PortMapping(container_port=4317, protocol=ecs.Protocol.TCP),  # gRPC
            ecs.PortMapping(container_port=4318, protocol=ecs.Protocol.TCP),  # HTTP
            ecs.PortMapping(container_port=13133, protocol=ecs.Protocol.TCP),  # health check
        )

        # ---------------------------------------------------------------
        # Fargate Service for OpenTelemetry Collector
        # ---------------------------------------------------------------
        otel_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "OtelService",
            cluster=cluster,
            task_definition=otel_task_def,
            service_name=f"{stack_prefix}-otel-collector",
            public_load_balancer=True,
            desired_count=1,
            assign_public_ip=True,
            security_groups=[otel_sg],
            listener_port=4318,  # HTTP endpoint
            open_listener=True,
        )

        # Configure health check (OTel health_check extension on port 13133)
        otel_service.target_group.configure_health_check(
            path="/",
            port="13133",
            healthy_threshold_count=2,
            unhealthy_threshold_count=3,
            timeout=cdk.Duration.seconds(5),
            interval=cdk.Duration.seconds(30),
        )

        # Log group cleanup — deletes orphaned log groups on stack destruction
        LogGroupCleanup(
            self,
            "LogGroupCleanup",
            log_group_prefixes=[
                f"/aws/ecs/containerinsights/{stack_prefix}/",
                f"/aws/lambda/{self.stack_name}-",
            ],
        )

        # ---------------------------------------------------------------
        # Outputs
        # ---------------------------------------------------------------
        cdk.CfnOutput(self, "VpcId", value=self._vpc.vpc_id)
        cdk.CfnOutput(
            self,
            "PublicSubnetIds",
            value=",".join([s.subnet_id for s in self._vpc.public_subnets]),
        )
        cdk.CfnOutput(
            self,
            "PhoenixUrl",
            value=f"http://{phoenix_service.load_balancer.load_balancer_dns_name}",
            description="Arize Phoenix dashboard URL",
        )
        cdk.CfnOutput(
            self,
            "OtelCollectorEndpointHttp",
            value=f"http://{otel_service.load_balancer.load_balancer_dns_name}:4318",
            description="OpenTelemetry Collector HTTP endpoint",
        )
        cdk.CfnOutput(
            self,
            "PhoenixApiKeySecretArn",
            value=phoenix_api_key_secret.secret_arn,
            description="ARN of the Phoenix API key secret",
        )

    @property
    def vpc(self) -> ec2.Vpc:
        return self._vpc

    @property
    def cluster_name(self) -> str:
        """ECS cluster name for observability services."""
        return to_kebab_case(self.stack_name)
