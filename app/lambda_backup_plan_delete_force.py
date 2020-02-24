import logging, os

import boto3
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    backup_table = boto3.resource('dynamodb').Table(os.environ['backupDB'])
    selection_table = boto3.resource('dynamodb').Table(os.environ['selectionDB'])

    request = common.json_body_as_dict(event)

    arn = request['arn']
    region = request['region']

    backup = common.assume_role('backup', arn, region)

    backup_plan_id = request['BackupPlanId']
    
    selections = backup.list_backup_selections(BackupPlanId=backup_plan_id)['BackupSelectionsList']

    for selection in selections:
        selection_id = selection['SelectionId']

        common.delete_backup_selection(backup, selection_table, backup_plan_id, selection_id)

    return common.delete_backup_plan(backup, backup_table, backup_plan_id)
