import boto3

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

from . import common


def modify_rds_tags(
    selected_account=dict,
    instance_tag=str,
    rds_db_name=str,
    rds=list,
    require_delete=bool
):
    arn = selected_account['arn']
    region = selected_account['region']

    rds_table = boto3.resource('dynamodb').Table(rds_db_name)
    rds_client = common.assume_role(service='rds', role_arn=arn, region=region)

    for inst in rds:
        rds_name = list(inst.keys())[0]
        value = inst[rds_name]
        for rds_item in rds_client.describe_db_instances().get('DBInstances', []):
            if rds_name == rds_item['DBInstanceIdentifier']:
                db_arn = rds_item['DBInstanceArn']

                rds_obj = rds_table.query(
                    TableName=rds_db_name,
                    KeyConditionExpression=Key('rdsName').eq(rds_name),
                )['Items'][0]

                if value == True and require_delete == False:
                    try:
                        rds_client.add_tags_to_resource(
                            ResourceName=db_arn,
                            Tags=[instance_tag]
                        )
                    except ClientError as e:
                        return common.throw_error(F'Failed to modify rds {rds_name} - Error: {e}')

                    if not instance_tag in rds_obj['Tags']:
                        rds_obj['Tags'].append(instance_tag)

                        try:
                            rds_table.put_item(Item=rds_obj, ReturnValues='NONE')
                        except ClientError as e:
                            return common.throw_error(F'Failed to modify rds {rds_name} - Error: {e}')

                else:
                    tag_index = rds_obj['Tags'].index(instance_tag)

                    try:
                        rds_client.remove_tags_from_resource(
                            ResourceName=db_arn,
                            TagKeys=[
                                instance_tag['Key']
                            ]
                        )
                    except ClientError as e:
                        return common.throw_error(F'Failed to modify rds {rds_name} - Error: {e}')

                    try:
                        rds_table.update_item(
                            Key={
                                'rdsName': rds_name,
                            },
                            UpdateExpression=F'remove Tags[{tag_index}]'
                        )
                    except ClientError as e:
                        return common.throw_error(F'Failed to modify rds {rds_name} - Error: {e}')