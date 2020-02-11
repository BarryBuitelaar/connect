import datetime, boto3, os, json, logging, time, traceback
from botocore.exceptions import ClientError
import datetime, sys

from boto3.dynamodb.conditions import Key
from . import common

# Set the log format
logger = logging.getLogger()
for h in logger.handlers:
    logger.removeHandler(h)

h = logging.StreamHandler(sys.stdout)
FORMAT = ' [%(levelname)s]/%(asctime)s/%(name)s - %(message)s'
h.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(h)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    backup_selection_db_name = os.environ['backupSelectionDB']
    backup_table = boto3.resource("dynamodb").Table(backup_selection_db_name)

    request = common.json_body_as_dict(event)

    BackupPlanId = request['backupPlanId']
    ConditionKey = request['key']
    ConditionValue = request['value']
    SelectionName = request['selectionName']

    selected_account = request['selectedAccount']
    arn = selected_account['arn']
    region = selected_account['region']
    IamRoleArn = selected_account['backupDefaultServiceRole']

    backup_plan_client = common.assume_role(service='backup', role_arn=arn, region=region)

    try:
        response = backup_plan_client.create_backup_selection(
            BackupPlanId=BackupPlanId,
            BackupSelection={
                'SelectionName': SelectionName, 
                'IamRoleArn': IamRoleArn, 
                'ListOfTags': [{
                    'ConditionType': 'STRINGEQUALS', 
                    'ConditionKey': ConditionKey, 
                    'ConditionValue': ConditionValue
                }]
            })
        logger.info(f'{SelectionName} is created')
    except ClientError as e:
        logger.error(f'Could not create {SelectionName}: {e}')

    SelectionId = response['SelectionId']

    return _insert_item(backup_table, request, SelectionId)


def _insert_item(backup_table, request, SelectionId):
    BackupPlanId = request['backupPlanId']
    ConditionKey = request['key']
    ConditionValue = request['value']
    SelectionName = request['selectionName']
    SelectionType = request['selectionType']

    selected_account = request['selectedAccount']
    AccountId = selected_account['accountId']

    arn = selected_account['arn']
    region = selected_account['region']

    try:
        backup_table.put_item(
            Item={
                'SelectionId': SelectionId,
                'SelectionName': SelectionName,
                'SelectionType': SelectionType,
                'BackupPlanId': BackupPlanId,
                'TagKey': ConditionKey,
                'TagValue': ConditionValue,
                'AccountId': AccountId,
                'Arn': arn,
                'Region': region
            }
        )
    except ClientError as e:
        return common.return_response(body={
            "post_error": F"Could not put selection {SelectionId} into Dynamo: {e}"
        })

    return common.return_response(body={
        "post_succes": F"Backup plan: {BackupPlanId} is created"
    })
