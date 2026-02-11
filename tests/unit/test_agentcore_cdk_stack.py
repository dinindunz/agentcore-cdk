import aws_cdk as core
import aws_cdk.assertions as assertions

from agentcore_cdk.agentcore_cdk_stack import AgentcoreCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in agentcore_cdk/agentcore_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AgentcoreCdkStack(app, "agentcore-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
