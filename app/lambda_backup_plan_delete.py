import logging, os

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    backup_table = boto3.resource('dynamodb').Table(os.environ['backupDB'])

    backup_plan_id = event['pathParameters']['backupPlanId']

    backup_plan_response = backup_table.query(
        TableName=os.environ['backupDB'],
        KeyConditionExpression=Key('BackupPlanId').eq(backup_plan_id),
    )['Items'][0]

    arn = backup_plan_response['Arn']
    region = backup_plan_response['Region']

    backup_client = common.assume_role('backup', arn, region)

    return common.delete_backup_plan(backup_client, backup_table, backup_plan_id)
