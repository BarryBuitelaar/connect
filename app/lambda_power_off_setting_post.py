import boto3
import os

from botocore.exceptions import ClientError

from . import common

from app.fn_get_instances_helper import get_instances
from app.fn_modify_instances_tags import modify_instances_tags
from app.fn_modify_asg_tags import modify_asg_tags

def lambda_handler(event, context):
    request = common.json_body_as_dict(event)
    instances_db_name = os.environ['instancesDB']
    asg_db_name = os.environ['asgDB']

    make_tag = request['makeTag']
    require_delete = True if make_tag == False else False

    instance_tag = {
        'Key': 'power-off-daily',
        'Value': request['time']
    }

    selected_account = {
        "arn": request['arn'],
        "region": request['region']
    }

    if 'instanceId' in request:
        instanceId = request['instanceId']

        inst_obj = {}
        inst_obj[instanceId] = make_tag

        instance_list=[]
        instance_list.append(inst_obj)

        try:
            modify_instances_tags(
                selected_account=selected_account,
                instance_tag=instance_tag,
                instances_db_name=instances_db_name,
                instances=instance_list,
                require_delete=require_delete,
                tag_key="power-off-daily"
            )
        except ClientError as e:
            return common.throw_error(F"Failed to set setting on {instanceId} Error: {e}")

    if 'asgName' in request:
        asg_name = request['asgName']

        try:
           modify_asg_tags(
                request,
                asg_db_name=asg_db_name,
                instances_db_name=instances_db_name,
                instance_tag=instance_tag,
                require_delete=require_delete
            )
        except ClientError as e:
            return common.throw_error(F"Failed to set setting on {asg_name} Error: {e}")


    return common.return_response(body={'post': 'success'})
