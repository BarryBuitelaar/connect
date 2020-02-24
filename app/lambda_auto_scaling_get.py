import os

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from . import common


def lambda_handler(event, context):
    asg_table = boto3.resource("dynamodb").Table(os.environ['asgDB'])

    try:
        response = asg_table.scan(
            TableName=os.environ['asgDB']
        )
    except ClientError as e:
        common.throw_error(F'Could not scan table of ASG\'s')

    return common.return_response(body=response['Items'])
