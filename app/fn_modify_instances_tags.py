import boto3
from botocore.exceptions import ClientError

from boto3.dynamodb.conditions import Key

from . import common


def modify_instances_tags(
    selected_account=dict,
    instance_tag=dict,
    instances_db_name=str,
    instances=list,
    require_delete=bool,
    tag_key=str
):
    arn = selected_account['arn']
    region = selected_account['region']

    instances_table = boto3.resource("dynamodb").Table(instances_db_name)
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
                return common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")

            if not instance_tag in instance_obj['Tags']:
                instance_obj['Tags'].append(instance_tag)

                try:
                    instances_table.put_item(Item=instance_obj, ReturnValues='NONE')
                except ClientError as e:
                    return common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")

        else:
            if instance_tag in instance_obj['Tags']:
                modified_tag = instance_tag
                tag_index = instance_obj['Tags'].index(instance_tag)
            else:
                modified_tag = {
                    'Key': tag_key,
                    'Value': instance_tag['Value']
                }
                tag_index = instance_obj['Tags'].index(modified_tag)

            try:
                ec2_client.delete_tags(
                    DryRun=False,
                    Resources=[
                        instance_id,
                    ],
                    Tags=[modified_tag]
                )
            except ClientError as e:
                return common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")

            try:
                instances_table.update_item(
                    Key={
                        "instanceId": instance_id,
                    },
                    UpdateExpression=F"remove Tags[{tag_index}]"
                )
            except ClientError as e:
                return common.throw_error(F"Failed to modify instance {instance_id} - Error: {e}")