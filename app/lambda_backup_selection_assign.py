import os, logging

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from . import common

from app.fn_modify_asg_tags import modify_asg_tags
from app.fn_modify_tags import modify_tags
from app.fn_get_backup_values import get_backup_values
from app.fn_get_client import get_client


def lambda_handler(event, context):
    backup_selection_db_name = os.environ['backupSelectionDB']
    instances_db_name = os.environ['instancesDB']
    asg_db_name = os.environ['asgDB']

    backup_selection_table = boto3.resource("dynamodb").Table(backup_selection_db_name)

    request = common.json_body_as_dict(event)

    selection_id = request['SelectionId']
    tag_key = request['TagKey']
    instances = request['instances']
    auto_scaling_groups = request['autoScalingGroups']

    tags = {
      'Key': tag_key,
      'Value': 'True'
    }

    modify_asg_tags(request, asg_db_name=asg_db_name, instances_db_name=instances_db_name, instance_tag=tags)

    return _instert_item(
        auto_scaling_groups,
        instances,
        tag_key,
        selection_id,
        backup_selection_table,
        backup_selection_db_name
    )


def _instert_item(auto_scaling_groups, instances, tag_key, selection_id, backup_selection_table, backup_selection_db_name):
    def helper(items, table_item):
        for item in items:
            backup_selection_obj = backup_selection_table.query(
                TableName=backup_selection_db_name,
                KeyConditionExpression=Key("SelectionId").eq(selection_id),
            )['Items'][0]
            id = list(item.keys())[0]
            value = item[id]

            if value == True:
                if table_item in backup_selection_obj:
                    backup_selection_obj[table_item].append({ id: True  })
                else:
                    backup_selection_obj[table_item] = [{ id: True  }]
    
                try:
                    backup_selection_table.put_item(Item=backup_selection_obj, ReturnValues='NONE')
                except ClientError as e:
                    common.throw_error(F"Failed to append {id} - Error: {e}")
            else:
                tag_index_bs = backup_selection_obj[table_item].index({ id: True })

                try:
                    backup_selection_table.update_item(
                        Key={
                            "SelectionId": selection_id,
                        },
                        UpdateExpression=F"remove {table_item}[{tag_index_bs}]"
                    )
                except ClientError as e:
                    common.throw_error(F"Failed to modify {id} - Error: {e}")

    helper(auto_scaling_groups, 'AutoScalingGroups')
    helper(instances, 'Instances')

    return common.return_response(body={
        "post_success": "Modified instance(s)"
    })