import boto3
import os

from boto3.dynamodb.conditions import Key

from . import common

def lambda_handler(event, context):
    rds_table = boto3.resource("dynamodb").Table(os.environ['rdsDB'])

    response = rds_table.scan(
        TableName=os.environ['rdsDB']
    )

    return common.return_response(body=response['Items'])
