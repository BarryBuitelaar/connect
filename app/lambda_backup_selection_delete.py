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

    backup_table = boto3.resource('dynamodb').Table(backup_selection_db_name)
    instances_table = boto3.resource('dynamodb').Table(instances_db_name)
    asg_table = boto3.resource('dynamodb').Table(asg_db_name)

    request = common.json_body_as_dict(event)

    arn = request['arn']
    region = request['region']

    BackupPlanId = request['backupPlanId']
    SelectionId = request['selectionId']

    backup_table_response = backup_table.query(
        TableName=backup_selection_db_name,
        KeyConditionExpression=Key('SelectionId').eq(SelectionId),
    )['Items'][0]

    backup_plan_client = common.assume_role(service='backup', role_arn=arn, region=region)

    common.delete_backup_selection(backup_plan_client, backup_table, BackupPlanId, SelectionId)

    if 'Instances' in backup_table_response:
        _remove_instance_tags(backup_table_response, request, instances_db_name)

    if 'AutoScalingGroups' in backup_table_response:
        _remove_asg_tags(backup_table_response, request, asg_db_name)

    return common.delete_backup_selection_db(backup_selection_db_name, SelectionId)


def _remove_instance_tags(backup_table_response, request, instances_db_name):
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


def _remove_asg_tags(backup_table_response, request, asg_db_name):
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
