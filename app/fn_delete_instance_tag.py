import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from app.fn_get_client import get_client

from . import common

def delete_instance_tag(items, tag_key, table, table_name, table_item):
    for item in items:
        id = list(item.keys())[0]

        table_obj = table.query(
            TableName=table_name,
            KeyConditionExpression=Key(table_item).eq(id),
        )['Items'][0]

        tag = {'Key': tag_key, 'PropagateAtLaunch': True, 'ResourceId': id, 'ResourceType': 'auto-scaling-group', 'Value': 'True'} if table_item == 'asgName' else {'Key': tag_key, 'Value': 'True'}

        tag_index = table_obj['Tags'].index(tag)

        ec2_client = common.assume_role(service='ec2', role_arn=table_obj['arn'], region=table_obj['region'])

        try:
            ec2_client.delete_tags(
                DryRun=False,
                Resources=[
                    id,
                ],
                Tags=[tag]
            )
        except ClientError as e:
            common.throw_error(F"Failed to delete tag on instance: {id} - Error: {e}")

        try:
            table.update_item(
                Key={
                    table_item: id,
                },
                UpdateExpression=F"remove Tags[{tag_index}]"
            )
        except ClientError as e:
            common.throw_error(F"Failed to delete tag {tag_key} on instance {id} - Error: {e}")