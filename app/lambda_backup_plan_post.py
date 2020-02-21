import os, logging

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    backup_table = boto3.resource('dynamodb').Table(os.environ['backupDB'])

    request = common.json_body_as_dict(event)

    backup_plan_name = request['backupplanname']
    backup_rule_name = request['backuprulename']
    schedule = request['schedule']
    retention = int(request['retention'])
    replication = request['replication']

    selected_account = request['selectedAccount']
    account_id = selected_account['accountId']

    backup_client = common.assume_role(service='backup', role_arn=selected_account['arn'], region=selected_account['region'])

    BackupPlan = {
        'BackupPlanName': backup_plan_name, 
        'Rules': [
            {
            'RuleName': backup_rule_name, 
            'TargetBackupVaultName': 'Default', 
            'ScheduleExpression': schedule, 
            'StartWindowMinutes': 60, 
            'CompletionWindowMinutes': 240, 
            'Lifecycle': {'DeleteAfterDays': retention}
            }
        ]
    }

    if replication == True:
        ReplRegion = request['repl_region']
        ReplRetention = int(request['repl_retention']) if request['replication'] else None
        CopyVaultArn = F'arn:aws:backup:{ReplRegion}:{account_id}:backup-vault:Default'

        BackupPlan['Rules'][0]['CopyActions'] = [{
            'Lifecycle': {'DeleteAfterDays': ReplRetention},
            'DestinationBackupVaultArn': CopyVaultArn
        }]

    try:
        response = backup_client.create_backup_plan(BackupPlan=BackupPlan)
    except ClientError as e:
        logger.error(F'ERROR: Could not create {backup_plan_name}: {e}')
        return common.return_response(body={
            'post_error': F'Backup {backup_plan_name} error {e}'
        })

    BackupPlanId = response['BackupPlanId']

    return _insert_item(BackupPlanId, backup_table, request)


def _insert_item(BackupPlanId, backup_table, request):
    Item = {
        'BackupPlanId': BackupPlanId,
        'BackupPlanName': request['backupplanname'],
        'Schedule': request['schedule'],
        'Retention': request['retention'],
        'Replication': request['replication'],
        'PeriodInString': request['periodInString'],
        'AccountId': request['selectedAccount']['accountId'],
        'AccountAlias': request['selectedAccount']['accountAlias'],
        'Arn': request['selectedAccount']['arn'],
        'Region': request['selectedAccount']['region']
    }

    if request['replication'] == True:
        Item['ReplRegion'] = request['repl_region']
        Item['ReplRetention'] = request['repl_retention']

    try:
        backup_table.put_item(Item=Item)
    except ClientError as e:
        logger.error(F'Could not insert backup {BackupPlanId} into Dynamo: {e}')
        return common.return_response(body={
            'post_error': F'Backup {request["backupplanname"]} error {e}'
        })

    return common.return_response(body={
        'post_success': F'Backup plan: {request["backupplanname"]} is created'
    })
