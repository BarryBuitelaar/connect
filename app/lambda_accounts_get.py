import os

import boto3
from boto3.dynamodb.conditions import Key

from . import common


def lambda_handler(event, context):
    accounts_table = boto3.resource("dynamodb").Table(os.environ['accountsDB'])

    response = accounts_table.scan(
        TableName=os.environ['accountsDB']
    )

    return common.return_response(body=response['Items'])
