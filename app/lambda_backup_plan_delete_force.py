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

    if len(selections) > 0:
        for selection in selections:
            selection_id = selection['SelectionId']
            
            try:
                backup.delete_backup_selection(
                    BackupPlanId=backup_plan_id,
                    SelectionId=selection_id
                )
            except ClientError as e:
                common.throw_error(F'Could not delete {selection_id} for backup {backup_plan_id}: {e}')
            else:
                _delete_backup_selection_db(selection_table, selection_id)

        logger.info(F'All selections for backup plan {backup_plan_id} removed')
        
    try:    
        response = backup.delete_backup_plan(BackupPlanId=backup_plan_id)
        logger.info(F'{backup_plan_id} is deleted')
    except ClientError as e:
        common.throw_error(F'Could not delete {backup_plan_id}: {e}')
    else:
        _delete_backup_plan_db(backup_table, backup_plan_id)

    return common.return_response(body={'post': 'success'})


def _delete_backup_plan_db(backup_table, backup_plan_id):
    try:
        backup_table.delete_item(
            Key={
                'BackupPlanId': backup_plan_id
            }
        )
    except ClientError as e:
        return common.throw_error(F'Could not delete BackupPlan {backup_plan_id} from table: {e}')


def _delete_backup_selection_db(selection_table, selection_id):
    try:
        selection_table.delete_item(
            Key={
                'SelectionId': selection_id
            }
        )
    except ClientError as e:
        return common.throw_error(F'Could not delete BackupSelection {selection_id} from table: {e}')
