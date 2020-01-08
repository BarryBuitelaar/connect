import boto3
import os

from boto3.dynamodb.conditions import Key

from . import common

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable')
    table = boto3.resource("dynamodb").Table(dynamo_DB)

    request = common.json_body_as_dict(event)

    data_type = request['type']

    response = table.query(
        TableName=dynamo_DB,
        KeyConditionExpression=Key("type").eq(data_type),
    )

    return common.return_response(body=response['Items'])
