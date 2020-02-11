import boto3
import os

from boto3.dynamodb.conditions import Key

from . import common


def lambda_handler(event, context):
    asg_table = boto3.resource("dynamodb").Table(os.environ['accountsDB'])

    response = asg_table.scan(
        TableName=os.environ['accountsDB']
    )

    return common.return_response(body=response['Items'])
