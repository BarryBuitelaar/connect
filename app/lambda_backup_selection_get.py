import boto3
import os
import logging
import datetime, sys

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger()
for h in logger.handlers:
    logger.removeHandler(h)

h = logging.StreamHandler(sys.stdout)
FORMAT = ' [%(levelname)s]/%(asctime)s/%(name)s - %(message)s'
h.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(h)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    global logger
    backup_selection_db_name = os.environ['backupSelectionDB']
    backup_selection_table = boto3.resource("dynamodb").Table(backup_selection_db_name)

    try:
      response = backup_selection_table.scan(
          TableName=backup_selection_db_name
      )
    except ClientError as e:
      logger.error(F"Received error:{e}")


    return common.return_response(body=response['Items'])
