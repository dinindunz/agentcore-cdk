#!/usr/bin/env python3
import os

import aws_cdk as cdk

from agentcore_cdk import AgentcoreCdkStack


app = cdk.App()
AgentcoreCdkStack(app, "AgentcoreCdkStack")

app.synth()
