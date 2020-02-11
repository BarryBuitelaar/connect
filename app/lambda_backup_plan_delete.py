import datetime, boto3, os, json, logging, time, traceback
from botocore.exceptions import ClientError
import datetime, sys

from boto3.dynamodb.conditions import Key

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
    backup_table = boto3.resource("dynamodb").Table(os.environ['backupDB'])

    BackupPlanId = event['pathParameters']['backupPlanId']

    backup_plan_response = backup_table.query(
        TableName=os.environ['backupDB'],
        KeyConditionExpression=Key("BackupPlanId").eq(BackupPlanId),
    )['Items'][0]

    arn = backup_plan_response['Arn']
    region = backup_plan_response['Region']

    backup_client = common.assume_role('backup', arn, region)

    try:
        backup_client.delete_backup_plan(BackupPlanId=BackupPlanId)
        logger.info(f'{BackupPlanId} is deleted')
    except ClientError as e:
        logger.error(f'Could not delete {BackupPlanId}: {e}')
        return common.return_response(body={
            "post_error": f'Could not delete {BackupPlanId}: {e}'
        })

    return _delete_item(backup_table, BackupPlanId)


def _delete_item(backup_table, BackupPlanId):
    try:
        backup_table.delete_item(
            Key={
                'BackupPlanId': BackupPlanId
            }
        )
    except ClientError as e:
        logger.error(f'Could not delete BackupPlan {BackupPlanId}: {e}')
        return common.return_response(body={
          "post_error": f'Could not delete {BackupPlanId}: {e}'
        })

    return common.return_response(body={
      "post_success": f'{BackupPlanId} is deleted'
    })
