import boto3
import os
import json

from boto3.dynamodb.conditions import Key

from . import common

from app.fn_get_instances_helper import get_instances
from app.fn_modify_tags import modify_tags
from app.fn_get_tag_values import get_tag_values
from app.fn_get_client import get_client
from app.fn_modify_asg_tags import modify_asg_tags
from app.fn_get_tag_values import get_tag_values
from app.fn_modify_instances_tags import modify_instances_tags
from app.fn_modify_rds_tags import modify_rds_tags

def lambda_handler(event, context):
    instances_db_name = os.environ['instancesDB']
    asg_db_name = os.environ['asgDB']
    rds_table_name = os.environ['rdsDB']
    db = os.environ['db']
    region = os.environ['region']

    asg_table = boto3.resource('dynamodb').Table(asg_db_name)
    instances_table = boto3.resource('dynamodb').Table(instances_db_name)
    rds_table = boto3.resource('dynamodb').Table(rds_table_name)

    config_table_name = common.get_table(db, 'ConfigTable')
    config_table = boto3.resource('dynamodb').Table(config_table_name)

    request = common.json_body_as_dict(event)

    item_key = request['item']
    tag_key = request['TagKey']

    tables = {
        'asgName': asg_table,
        'rdsName': rds_table,
        'instanceId': instances_table
    }

    table_key = item_key
    table = tables[table_key]

    if item_key == 'asgName':
        modify_asg_tags(
            request,
            asg_db_name=asg_db_name,
            instances_db_name=instances_db_name,
            instance_tag={'Key': 'ASGSchedule', 'Value': tag_key},
            require_delete=False
        )

    else:
        schedule_table = config_table.query(
            TableName=config_table_name,
            KeyConditionExpression=Key('type').eq('schedule'),
        )['Items']

        tag_keys = list(map(lambda e: e['name'], schedule_table))
        tag_values = get_tag_values(request, tag_keys)

        item = item_key

        response = table.get_item(Key={ item: request[item] })['Item']
        tag_value = list(tag_values[0].keys())[0]
        require_delete = False if tag_values[0][tag_value] == True else True

        instanceId = response['instanceId'] if 'instanceId' in response else response['rdsName']

        inst_obj = {}
        inst_obj[instanceId] = tag_values[0][tag_value]

        instance_list=[]
        instance_list.append(inst_obj)

        selected_account = {
            'arn': response['arn'],
            'region': response['region']
        }

        tags = modify_tags(
            response={'Tags': list()},
            tag_values=tag_values,
            tag_for_asg=False,
            tag_for_aws=True
        )

        for tag in tags['Tags']:
            modified_tag = {
                'Key': 'AWSSchedule',
                'Value': tag['Value']
            }

            if item_key == 'instanceId':
                modify_instances_tags(
                    selected_account=selected_account,
                    instance_tag=modified_tag,
                    instances_db_name=instances_db_name,
                    instances=instance_list,
                    require_delete=require_delete,
                    tag_key='AWSSchedule'
                )

            if item == 'rdsName':
                modify_rds_tags(
                    selected_account=selected_account,
                    instance_tag=modified_tag,
                    rds_db_name=rds_table_name,
                    rds=instance_list,
                    require_delete=require_delete
                )

    return common.return_response(body={'post': 'success'})
