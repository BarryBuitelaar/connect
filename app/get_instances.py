import boto3;
import os;

from boto3.dynamodb.conditions import Key;

from . import common;

def lambda_handler(event, context):
    instances_table = boto3.resource("dynamodb").Table(os.environ['instancesDB']);

    response = instances_table.scan(
        TableName=os.environ['instancesDB']
    );

    return common.return_response(body=response['Items']);
