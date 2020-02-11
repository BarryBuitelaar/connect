import boto3
from botocore.exceptions import ClientError

from boto3.dynamodb.conditions import Key

from . import common


def modify_asg_tags(request, **kwargs):
    tag_key = request['TagKey']
    selected_account = request['selectedAccount']

    arn = selected_account['arn']
    region = selected_account['region']

    require_delete = 'delete' in kwargs if True else False

    if 'autoScalingGroups' in request:
        asg_db_name = kwargs['asg_db_name']
        asg_table = boto3.resource("dynamodb").Table(asg_db_name)
        auto_scaling_groups = request['autoScalingGroups']
        auto_scaling_client = common.assume_role(service='autoscaling', role_arn=arn, region=region)

        for asg in auto_scaling_groups:
            key = list(asg.keys())[0]

            asg_obj = asg_table.query(
                TableName=asg_db_name,
                KeyConditionExpression=Key("asgName").eq(key),
            )['Items'][0]

            newTag = {
                    'ResourceId': key,
                    'ResourceType': 'auto-scaling-group',
                    'Key': tag_key,
                    'Value': 'True',
                    'PropagateAtLaunch': True
                }

            if asg[key] == True and require_delete == False:
                try:
                    auto_scaling_client.create_or_update_tags(
                        Tags=[newTag]
                    )
                    asg_obj['Tags'].append(newTag)
                    asg_table.put_item(
                        Item=asg_obj,
                        ReturnValues='NONE'
                    )
                except ClientError as e:
                    common.throw_error(F"Failed to modify auto scaling group {key} tag {tag_key} - Error: {e}")
            else:
                try:
                    auto_scaling_client.delete_tags(
                        Tags=[newTag]
                    )
                    tag_index = asg_obj['Tags'].index(newTag)
                    asg_table.update_item(
                        Key={
                            "asgName": key,
                        },
                        UpdateExpression=F"remove Tags[{tag_index}]"
                    )

                except ClientError as e:
                    common.throw_error(F"Failed to delete auto scaling group {key} tag {tag_key} - Error: {e}")

    if 'instances' in request:
        instances_db_name = kwargs['instances_db_name']
        instance_tag = kwargs['instance_tag']
        instances_table = boto3.resource("dynamodb").Table(instances_db_name)
        instances = request['instances']
        ec2_client = common.assume_role(service='ec2', role_arn=arn, region=region)

        for inst in instances:
            instance_id = list(inst.keys())[0]
            value = inst[instance_id]

            instance_obj = instances_table.query(
                TableName=instances_db_name,
                KeyConditionExpression=Key("instanceId").eq(instance_id),
            )['Items'][0]

            if value == True and require_delete == False:
                try:
                    ec2_client.create_tags(
                        DryRun=False,
                        Resources=[
                            instance_id,
                        ],
                        Tags=[instance_tag]
                    )
                except ClientError as e:
                    common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")

                if not instance_tag in instance_obj['Tags']:
                    instance_obj['Tags'].append(instance_tag)

                    try:
                        instances_table.put_item(Item=instance_obj, ReturnValues='NONE')
                    except ClientError as e:
                        common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")

            else:
                tag_index = instance_obj['Tags'].index(instance_tag)

                try:
                    ec2_client.delete_tags(
                        DryRun=False,
                        Resources=[
                            instance_id,
                        ],
                        Tags=[instance_tag]
                    )
                except ClientError as e:
                    common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")

                try:
                    instances_table.update_item(
                        Key={
                            "instanceId": instance_id,
                        },
                        UpdateExpression=F"remove Tags[{tag_index}]"
                    )
                except ClientError as e:
                    common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")