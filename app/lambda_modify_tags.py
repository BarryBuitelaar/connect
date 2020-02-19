import boto3
import os
import json

from boto3.dynamodb.conditions import Key

from . import common

from app.fn_get_instances_helper import get_instances
from app.fn_modify_instances import modify_instance
from app.fn_modify_tags import modify_tags
from app.fn_get_backup_values import get_backup_values
from app.fn_get_client import get_client
from app.fn_modify_asg_tags import modify_asg_tags

def lambda_handler(event, context):
    instances_db_name = os.environ['instancesDB']
    asg_db_name = os.environ['asgDB']
    rds_table_name = os.environ['rdsDB']
    db = os.environ['db']
    region = os.environ['region']

    asg_table = boto3.resource("dynamodb").Table(asg_db_name)
    instances_table = boto3.resource("dynamodb").Table(instances_db_name)
    rds_table = boto3.resource("dynamodb").Table(rds_table_name)

    config_table_name = common.get_table(db, 'ConfigTable')
    config_table = boto3.resource("dynamodb").Table(config_table_name)

    request = common.json_body_as_dict(event)

    item_key = request['item']
    tag_key = request['TagKey']

    table_key = item_key
    tables = {
        'asgName': asg_table,
        'rdsName': rds_table,
        'instanceId': instances_table
    }

    schedule_table = config_table.query(
        TableName=config_table_name,
        KeyConditionExpression=Key("type").eq("schedule"),
    )['Items']

    backup_keys = list(map(lambda e: e["name"], schedule_table))
    backup_values = get_backup_values(request, backup_keys)

    if item_key == 'asgName':
        modify_asg_tags(request, asg_db_name=asg_db_name, instances_db_name=instances_db_name, instance_tag={'Key': 'ASGSchedule', 'Value': tag_key})

    else:
        modify_instance(
            item=item_key,
            request=request,
            table=tables[table_key],
            backup_values=backup_values,
            db=db,
            region=region
        )

    return common.return_response(body={'post': 'success'})
