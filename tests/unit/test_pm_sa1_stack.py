import aws_cdk as core
import aws_cdk.assertions as assertions

from pm_sa1.pm_sa1_stack import PmSa1Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in pm_sa1/pm_sa1_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PmSa1Stack(app, "pm-sa1")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
