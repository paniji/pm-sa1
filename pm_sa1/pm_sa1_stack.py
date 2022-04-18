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

class PmSa1Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create dynamo table
        demo_table = aws_dynamodb.Table(
            self, "demo_table",
            partition_key=aws_dynamodb.Attribute(
                name="id",
                type=aws_dynamodb.AttributeType.STRING
            )
        )

        # create producer lambda function
        producer_lambda = aws_lambda.Function(self, "producer_lambda_function",
                                              runtime=aws_lambda.Runtime.PYTHON_3_6,
                                              handler="lambda_function.lambda_handler",
                                              code=aws_lambda.Code.from_asset("./lambda/producer"))

        producer_lambda.add_environment("TABLE_NAME", demo_table.table_name)

        # grant permission to lambda to write to demo table
        demo_table.grant_write_data(producer_lambda)

        # create consumer lambda function
        consumer_lambda = aws_lambda.Function(self, "consumer_lambda_function",
                                              runtime=aws_lambda.Runtime.PYTHON_3_6,
                                              handler="lambda_function.lambda_handler",
                                              code=aws_lambda.Code.from_asset("./lambda/consumer"))

        consumer_lambda.add_environment("TABLE_NAME", demo_table.table_name)

        # grant permission to lambda to read from demo table
        demo_table.grant_read_data(consumer_lambda)

        base_api = _apigw.RestApi(self, '_apigwWithCors',
                                  rest_api_name='_apigwWithCors')

        example_entity = base_api.root.add_resource(
            'example',
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_methods=['GET', 'POST', 'OPTIONS'],
                allow_origins=_apigw.Cors.ALL_ORIGINS)
        )

        entity1 = base_api.root.add_resource(
            'hello',
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_methods=['GET', 'OPTIONS'],
                allow_origins=_apigw.Cors.ALL_ORIGINS)
        )

        example_entity_get_lambda_integration = _apigw.LambdaIntegration(
            consumer_lambda,
            proxy=False,
            #passthrough_behavior=_apigw.PassthroughBehavior.NEVER,
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                }
            }]
        )

        example_entity.add_method(
            'GET', example_entity_get_lambda_integration,
            
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': True,
                }
            }]
        )

        # We define the JSON Schema for the transformed valid response
        response_model = base_api.add_model("ResponseModel",
            content_type="application/json",
            model_name="ResponseModel",
            schema=_apigw.JsonSchema(
                schema=_apigw.JsonSchemaVersion.DRAFT4,
                title="pollResponse",
                type=_apigw.JsonSchemaType.OBJECT,
                properties={
                    "state": _apigw.JsonSchema(type=_apigw.JsonSchemaType.STRING),
                    "greeting": _apigw.JsonSchema(type=_apigw.JsonSchemaType.STRING)
                }
            )
        )

        error_model = base_api.add_model("errorResponseModel",
            content_type="application/json",
            model_name="errorResponseModel",
            schema=_apigw.JsonSchema(
                schema=_apigw.JsonSchemaVersion.DRAFT4,
                title="errorResponse",
                type=_apigw.JsonSchemaType.OBJECT,
                properties={
                    "state": _apigw.JsonSchema(type=_apigw.JsonSchemaType.STRING),
                    "greeting": _apigw.JsonSchema(type=_apigw.JsonSchemaType.STRING)
                }
            )
        )

        integration = _apigw.LambdaIntegration(producer_lambda,
            proxy=False,
            request_parameters={
                "integration.request.querystring.who": "method.request.querystring.who"
            },
            allow_test_invoke=True,
            request_templates={
                "application/json": json.dumps({"action": "sayHello", "poll_id": "$util.escapeJavaScript($input.params('who'))"})
            },
            passthrough_behavior=_apigw.PassthroughBehavior.NEVER,
            integration_responses=[_apigw.IntegrationResponse(
                status_code="200",
                response_templates={
                    "application/json": json.dumps({"state": "ok", "greeting": "$util.escapeJavaScript($input.body)"})
                },
                response_parameters={
                    "method.response.header._content-_type": "'application/json'",
                    "method.response.header._access-_control-_allow-_origin": "'*'",
                    "method.response.header._access-_control-_allow-_credentials": "'true'"
                }
            ), _apigw.IntegrationResponse(
                selection_pattern="""(
                |.)+""",
                status_code="400",
                response_templates={
                    "application/json": json.dumps({"state": "error", "message": "$util.escapeJavaScript($input.path('$.errorMessage'))"})
                },
                response_parameters={
                    "method.response.header._content-_type": "'application/json'",
                    "method.response.header._access-_control-_allow-_origin": "'*'",
                    "method.response.header._access-_control-_allow-_credentials": "'true'"
                }
            )
            ]
        )

        example_entity.add_method("POST", integration,
            # We can mark the parameters as required
            request_parameters={
                "method.request.querystring.who": True
            },
            # we can set request validator options like below
            request_validator_options=_apigw.RequestValidatorOptions(
                request_validator_name="test-validator",
                validate_request_body=True,
                validate_request_parameters=False
            ),
            method_responses=[_apigw.MethodResponse(
                # Successful response from the integration
                status_code="200",
                # Define what parameters are allowed or not
                response_parameters={
                    "method.response.header._content-_type": True,
                    "method.response.header._access-_control-_allow-_origin": True,
                    "method.response.header._access-_control-_allow-_credentials": True
                },
                # Validate the schema on the response
                response_models={
                    "application/json": response_model
                }
            ), _apigw.MethodResponse(
                # Same thing for the error responses
                status_code="400",
                response_parameters={
                    "method.response.header._content-_type": True,
                    "method.response.header._access-_control-_allow-_origin": True,
                    "method.response.header._access-_control-_allow-_credentials": True
                },
                response_models={
                    "application/json": error_model
                }
            )
            ]
        )