import logging, os, sys

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
    
    temp = backup.list_backup_plans()['BackupPlansList']
    backup_plan_ids = map(lambda el: el['BackupPlanId'], temp) # map elements to ids
    
    backup_plans = [get_backup_plan(backup, backup_plan_id) for backup_plan_id in backup_plan_ids]

    for backup_plan in backup_plans:
        backup_projection = project_backup(backup_plan)
        update_backup_plan_db(backup_table, backup_projection)

        selection_projection = project_selection(backup_plan['selections'])
        update_backup_selections_db(selection_table, selection_projection)


def get_backup_plan(backup, backup_plan_id):
    backup_plan = backup.get_backup_plan(BackupPlanId=backup_plan_id)
    
    backup_selections = backup.list_backup_selections(
        BackupPlanId=backup_plan_id
    )['BackupSelectionsList']

    # get all selections
    backup_selections = []

    backup_selections_ids = map(lambda el: el['SelectionId'], backup_selections)

    for backup_selection_id in backup_selections_ids:
        backup_selection = backup.get_backup_selection(
            BackupPlanId=backup_plan_id,
            SelectionId=backup_selection_id
        )

        backup_selections.append(backup_selection)

    backup_plan['selections'] = backup_selections

    return backup_plan


def project_backup(backup_plan):
    record = {
        'BackupPlanId': backup_plan['BackupPlanId'],
        'BackupPlanName': backup_plan['BackupPlan']['BackupPlanName'],
        'Retention': str(backup_plan['BackupPlan']['Rules'][0]['Lifecycle']['DeleteAfterDays']),
        'Schedule': backup_plan['BackupPlan']['Rules'][0]['ScheduleExpression']
    }
    
    rule = backup_plan['BackupPlan']['Rules'][0]

    if 'CopyActions' in rule:
        record['Replication'] = 'true'
        record['ReplRegion'] = rule['CopyActions'][0]['DestinationBackupVaultArn'].split(':')[3]
        record['ReplRetention'] = str(rule['CopyActions'][0]['Lifecycle']['DeleteAfterDays'])
    else:
        record['Replication'] = 'false'

    return record


def update_backup_plan_db(backup_table, projection):
    record_update = {
        ':backupplanname': projection['BackupPlanName'], 
        ':schedule': projection['Schedule'],
        ':retention': projection['Retention'],
        ':replication': projection['Replication'] 
    }

    update_expression = ('SET '
            'BackupPlanName = :backupplanname,'
            'Schedule = :schedule,'
            'Retention = :retention,'
            'Replication = :replication'
            )

    if projection['Replication'] == 'true':
        record_update[':replregion'] = projection['ReplRegion']
        record_update[':replretention'] = projection['ReplRetention']

        update_expression += ', ReplRegion = :replregion'
        update_expression += ', ReplRetention = :replretention'

    try:
        backup_table.update_item(
            Key={
                'BackupPlanId': projection['BackupPlanId']
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=record_update
        )
    except ClientError as e:
        return common.throw_error(F'Could not update {projection["BackupPlanId"]}')

    return common.return_response(body={'post': 'success'})


def project_selection(selections):
    return [
    {
        'SelectionId': item['SelectionId'],
        'BackupPlanId': item['BackupPlanId'],
        'SelectionName': item['BackupSelection']['SelectionName'],
        'TagKey': item['BackupSelection']['ListOfTags'][0]['ConditionKey'],
        'TagValue': item['BackupSelection']['ListOfTags'][0]['ConditionValue']
    } 
    for item in selections]


def update_backup_selections_db(selection_table, projection):
    error_count = 0

    for selection in projection:
        record_update = {
            ':backupplanid': selection['BackupPlanId'],
            ':selectionname': selection['SelectionName'],
            ':tagkey': selection['TagKey'],
            ':tagvalue': selection['TagValue']
        }
        
        update_expression = ('SET '
                'BackupPlanId = :backupplanid,'
                'SelectionName = :selectionname,'
                'TagKey = :tagkey,'
                'TagValue = :tagvalue'
                )

        try: 
            selection_table.update_item(
                Key={
                    'SelectionId': selection['SelectionId']
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=record_update
            )
        except ClientError as e:
            logger.error(F'Could not update selection {selection["SelectionId"]}: {e}')
            error_count += 1

    return common.return_response(body={'post': F'could not update {error_count} selections in table'})
