import logging, os

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    backup_table = boto3.resource("dynamodb").Table(os.environ['backupDB'])

    backup_plan_id = event['pathParameters']['backupPlanId']

    backup_plan_response = backup_table.query(
        TableName=os.environ['backupDB'],
        KeyConditionExpression=Key("BackupPlanId").eq(backup_plan_id),
    )['Items'][0]

    arn = backup_plan_response['Arn']
    region = backup_plan_response['Region']

    backup_client = common.assume_role('backup', arn, region)

    try:
        backup_client.delete_backup_plan(BackupPlanId=backup_plan_id)
        logger.info(F'{backup_plan_id} is deleted')
    except ClientError as e:
        logger.error(F'Could not delete {backup_plan_id}: {e}')
        return common.return_response(body={
            "post_error": F'Could not delete {backup_plan_id}: {e}'
        })

    return _delete_item(backup_table, backup_plan_id)


def _delete_item(backup_table, backup_plan_id):
    try:
        backup_table.delete_item(
            Key={
                'BackupPlanId': backup_plan_id
            }
        )
    except ClientError as e:
        logger.error(F'Could not delete BackupPlan {backup_plan_id}: {e}')
        return common.return_response(body={
          "post_error": F'Could not delete {backup_plan_id}: {e}'
        })

    return common.return_response(body={
      "post_success": F'{backup_plan_id} is deleted'
    })
