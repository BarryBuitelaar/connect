import os, logging

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    backup_selection_db_name = os.environ['backupSelectionDB']
    backup_selection_table = boto3.resource("dynamodb").Table(backup_selection_db_name)

    try:
      response = backup_selection_table.scan(
          TableName=backup_selection_db_name
      )
    except ClientError as e:
      logger.error(F"Received error:{e}")

    return common.return_response(body=response['Items'])
