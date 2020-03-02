import os, logging

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger()

def lambda_handler(event, context):
    global logger
    backup_table = boto3.resource('dynamodb').Table(os.environ['backupDB'])

    try:
        response = backup_table.scan(
            TableName=os.environ['backupDB']
        )
    except ClientError as e:
        logger.error(F'Received error: {e}')

    return common.return_response(body=response['Items'])
