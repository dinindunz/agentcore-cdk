"""
AgentCore Inference Profile construct.

Creates an Application Inference Profile with cost allocation tags for tracking
Bedrock model usage across environments, teams, and projects.
"""

import aws_cdk as cdk
from aws_cdk import CfnTag
from aws_cdk import aws_bedrock as bedrock
from aws_cdk import aws_ssm as ssm
from aws_cdk.aws_bedrock_alpha import ApplicationInferenceProfile
from constructs import Construct

from ..utils import to_kebab_case


class InferenceProfileConstruct(Construct):
    """
    Creates an Application Inference Profile with cost allocation tags.

    Inference profiles enable cost tracking and multi-region model access.
    Tags allow filtering costs in AWS Cost Explorer by environment, team, project, etc.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        profile_name: str,
        model_id: str,
        description: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        """
        Create an Application Inference Profile with cost allocation tags.

        Args:
            scope: CDK construct scope
            construct_id: Construct ID
            profile_name: Name for the inference profile (will be prefixed with stack name)
            model_id: Cross-region inference profile ID (e.g., au.anthropic.claude-sonnet-4-6)
            description: Optional description of the inference profile
            tags: Optional cost allocation tags (e.g., {"Environment": "prod", "Team": "AI"})
        """
        super().__init__(scope, construct_id)

        stack = cdk.Stack.of(self)
        stack_prefix = to_kebab_case(stack.stack_name)

        # Profile names use kebab-case convention
        prefixed_profile_name = f"{stack_prefix}-{to_kebab_case(profile_name)}"

        # Convert dict tags to CfnTag list
        cfn_tags = [CfnTag(key=key, value=value) for key, value in (tags or {}).items()]

        # Create L1 construct with full tag support
        # Use model_id directly as copy_from (supports cross-region inference profile IDs)
        self._cfn_profile = bedrock.CfnApplicationInferenceProfile(
            self,
            "Profile",
            inference_profile_name=prefixed_profile_name,
            model_source=bedrock.CfnApplicationInferenceProfile.InferenceProfileModelSourceProperty(
                copy_from=f"arn:aws:bedrock:{stack.region}:{stack.account}:inference-profile/{model_id}"
            ),
            description=description or f"Application inference profile: {prefixed_profile_name}",
            tags=cfn_tags,
        )

        # Import as L2 for easier integration with other constructs
        # L2 provides grant methods and better typing
        self.profile = ApplicationInferenceProfile.from_cfn_application_inference_profile(
            self._cfn_profile
        )

        # Export inference profile ARN to SSM for script access
        ssm_prefix = f"/{stack_prefix}"
        ssm.StringParameter(
            self,
            "ProfileArnParam",
            parameter_name=f"{ssm_prefix}/inference-profile-arn",
            string_value=self.inference_profile_arn,
            description=f"Inference profile ARN for {profile_name}",
        )

        ssm.StringParameter(
            self,
            "ProfileIdParam",
            parameter_name=f"{ssm_prefix}/inference-profile-id",
            string_value=self.inference_profile_id,
            description=f"Inference profile ID for {profile_name}",
        )

    @property
    def inference_profile_arn(self) -> str:
        """
        Inference profile ARN for use in Bedrock API calls.

        Use this ARN instead of the foundation model ARN when invoking models
        to ensure costs are tracked with the profile's tags.

        Returns:
            Inference profile ARN string
        """
        return self._cfn_profile.attr_inference_profile_arn

    @property
    def inference_profile_id(self) -> str:
        """
        Inference profile ID.

        Returns:
            Inference profile ID string
        """
        return self._cfn_profile.attr_inference_profile_id

    @property
    def inference_profile_name(self) -> str:
        """
        Inference profile name.

        Returns:
            Inference profile name string
        """
        return self._cfn_profile.inference_profile_name
