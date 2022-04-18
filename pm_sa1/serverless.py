from cgitb import handler
from aws_cdk import (
    aws_lambda,
    aws_dynamodb,
    aws_events,
    aws_events_targets,
    Duration, Stack,
    aws_apigateway as _apigw
)
from constructs import Construct
import json
import yaml

class Sls(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        with open('./serverless/manifest.yml') as file:
            #prime_service = yaml.safe_load(file)
            try:
                print(yaml.safe_load(file))
            except yaml.YAMLError as exc:
                print(exc)

        #print(prime_service['functions']['hello']['handler'])