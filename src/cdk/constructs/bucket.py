import os

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from ..utils import to_kebab_case


class BucketDeploymentConstruct(Construct):
    """S3 bucket with local asset deployment, auto-cleanup on stack deletion, and SSM bucket name parameter."""

    def __init__(
        self,
        scope: Construct,
        id: str,
        *,
        bucket_name: str,
        source_path: str,
    ) -> None:
        super().__init__(scope, id)

        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)
        bucket_name_kebab = to_kebab_case(bucket_name)

        ssm_prefix = f"/{stack_prefix}"
        ssm_param_key = f"{bucket_name_kebab}-bucket-name"
        prefixed_bucket_name = f"{stack_prefix}-{bucket_name_kebab}"

        self._bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=prefixed_bucket_name,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # __file__ is src/cdk/constructs/bucket.py — ../.. resolves to src/
        s3_deployment.BucketDeployment(
            self,
            "Deployment",
            sources=[
                s3_deployment.Source.asset(
                    os.path.join(os.path.dirname(__file__), "..", "..", source_path)
                )
            ],
            destination_bucket=self._bucket,
        )

        ssm.StringParameter(
            self,
            "BucketNameParam",
            parameter_name=f"{ssm_prefix}/{ssm_param_key}",
            string_value=prefixed_bucket_name,
        )

    @property
    def bucket(self) -> s3.Bucket:
        return self._bucket

    @property
    def bucket_name_value(self) -> str:
        """The prefixed bucket name (resolved at deploy time)."""
        return self._bucket.bucket_name
