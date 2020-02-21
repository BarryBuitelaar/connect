import os, logging

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from app.fn_get_client import get_client
from app.fn_modify_asg_tags import modify_asg_tags

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    backup_selection_db_name = os.environ['backupSelectionDB']
    instances_db_name = os.environ['instancesDB']
    asg_db_name = os.environ['asgDB']

    backup_table = boto3.resource("dynamodb").Table(backup_selection_db_name)
    instances_table = boto3.resource("dynamodb").Table(instances_db_name)
    asg_table = boto3.resource("dynamodb").Table(asg_db_name)

    BackupPlanId = event['pathParameters']['backupPlanId']
    SelectionId = event['pathParameters']['selectionId']

    request = common.json_body_as_dict(event)

    arn = request['arn']
    region = request['region']

    backup_table_response = backup_table.query(
        TableName=backup_selection_db_name,
        KeyConditionExpression=Key("SelectionId").eq(SelectionId),
    )['Items'][0]

    backup_plan_client = common.assume_role(service='backup', role_arn=arn, region=region)

    try:
        backup_plan_client.delete_backup_selection(BackupPlanId=BackupPlanId, SelectionId=SelectionId)
        logger.info(f'{SelectionId} is deleted')
    except ClientError as e:
        logger.error(f'Could not delete {SelectionId}: {e}')

    return _delete_item(request, backup_table_response, SelectionId, backup_table, backup_selection_db_name, instances_table, instances_db_name, asg_table, asg_db_name)


def _delete_item(request, backup_table_response, SelectionId, backup_table, backup_selection_db_name, instances_table, instances_db_name, asg_table, asg_db_name):
    if 'Instances' in backup_table_response:

        instances = backup_table_response['Instances']
        tag_key = backup_table_response['TagKey']

        new_request = {
            'selectedAccount': {
                'arn': request['arn'],
                'region': request['region']
            },
            'TagKey': tag_key,
            'instances': instances
        }

        tags = {
            'Key': tag_key,
            'Value': 'True'
        }

        modify_asg_tags(request=new_request, instances_db_name=instances_db_name, instance_tag=tags, delete=True)

    if 'AutoScalingGroups' in backup_table_response:
        asgs = backup_table_response['AutoScalingGroups']
        tag_key = backup_table_response['TagKey']

        new_request = {
            'selectedAccount': {
                'arn': request['arn'],
                'region': request['region']
            },
            'TagKey': tag_key,
            'autoScalingGroups': asgs
        }
        modify_asg_tags(request=new_request, asg_db_name=asg_db_name, delete=True)

    try:
        backup_table.delete_item(
            Key={
                'SelectionId': SelectionId
            }
        )
    except ClientError as e:
        common.throw_error(F'Could not delete {SelectionId} from Dynamo: {e}')

    return common.return_response(body={
      "post_success": F'{SelectionId} is deleted'
    })
