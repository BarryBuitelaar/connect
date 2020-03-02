import boto3

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from . import common
from app.fn_modify_instances_tags import modify_instances_tags
from app.fn_modify_rds_tags  import modify_rds_tags


def modify_asg_tags(request, **kwargs):
    tag_key = request['TagKey']
    selected_account = request['selectedAccount']

    arn = selected_account['arn']
    region = selected_account['region']

    require_delete = 'delete' in kwargs

    if 'autoScalingGroups' in request:
        _modify_asg_tags(kwargs, request, arn, region, tag_key, require_delete)

    if 'instances' in request:
        modify_instances_tags(
            selected_account=selected_account,
            instance_tag=kwargs['instance_tag'],
            instances_db_name=kwargs['instances_db_name'],
            instances=request['instances'],
            require_delete=require_delete,
            tag_key="ASGSchedule"
        )

    if 'rds' in request:
        modify_rds_tags(
            selected_account=selected_account,
            instance_tag=kwargs['instance_tag'],
            rds_db_name=kwargs['rds_db_name'],
            rds=request['rds'],
            require_delete=require_delete
        )


def _modify_asg_tags(kwargs, request, arn, region, tag_key, require_delete):
    asg_db_name = kwargs['asg_db_name']
    asg_table = boto3.resource('dynamodb').Table(asg_db_name)
    auto_scaling_groups = request['autoScalingGroups']
    auto_scaling_client = common.assume_role(service='autoscaling', role_arn=arn, region=region)

    for asg in auto_scaling_groups:
        key = list(asg.keys())[0]

        asg_obj = asg_table.query(
            TableName=asg_db_name,
            KeyConditionExpression=Key('asgName').eq(key),
        )['Items'][0]

        newTag = {
                'ResourceId': key,
                'ResourceType': 'auto-scaling-group',
                'Key': tag_key,
                'Value': 'True',
                'PropagateAtLaunch': True
            }

        if asg[key] and not require_delete:
            try:
                auto_scaling_client.create_or_update_tags(
                    Tags=[newTag]
                )
                asg_obj['Tags'].append(newTag)
                asg_table.put_item(
                    Item=asg_obj
                )
            except ClientError as e:
                common.throw_error(F'Failed to modify auto scaling group {key} tag {tag_key}: {e}')
        else:
            try:
                auto_scaling_client.delete_tags(
                    Tags=[newTag]
                )
                tag_index = asg_obj['Tags'].index(newTag)
                asg_table.update_item(
                    Key={
                        'asgName': key,
                    },
                    UpdateExpression=F'remove Tags[{tag_index}]'
                )

            except ClientError as e:
                common.throw_error(F'Failed to delete auto scaling group {key} tag {tag_key}: {e}')
