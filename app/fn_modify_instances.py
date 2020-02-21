import os

import boto3
from boto3.dynamodb.conditions import Key

from . import common

from app.fn_modify_tags import modify_tags
from app.fn_get_backup_values import get_backup_values
from app.fn_get_client import get_client


def modify_instance(item, request, table, backup_values, db, region):
    response = table.get_item(Key={ item: request[item] })['Item']
    backup_value = list(backup_values[0].keys())[0]

    if backup_values[0][backup_value] == True:
        modification_response = modify_tags(
            response=response,
            backup_values=backup_values,
            tag_for_asg=False,
            tag_for_aws=True
        )
        table.put_item(Item=modification_response, ReturnValues='NONE')
    else:
        tag_index = response['Tags'].index({'Key':'AWSSchedule', 'Value': backup_value})

        table.update_item(
            Key={
                item: request[item],
            },
            UpdateExpression=F"remove Tags[{tag_index}]"
        )

    tags = modify_tags(
        response={'Tags': list()},
        backup_values=backup_values,
        tag_for_asg=False,
        tag_for_aws=True
    )

    for tag in tags['Tags']:
        modified_tag = {
            'Key': 'AWSSchedule',
            'Value': tag['Value']
        }
        if item == 'instanceId':
            ec2_client = common.assume_role(service='ec2', role_arn=response['arn'], region=response['region'])

            if backup_values[0][backup_value] == True:
                print('set tag', response['instanceId'], modified_tag)
                modification_for_instances_response = ec2_client.create_tags(
                    DryRun=False,
                    Resources=[
                        response['instanceId'],
                    ],
                    Tags=[modified_tag]
                )
            else:
                modification_for_instances_response = ec2_client.delete_tags(
                    DryRun=False,
                    Resources=[
                        response['instanceId'],
                    ],
                    Tags=[modified_tag]
                )
            # TODO check if the response is correct otherwise throw a error
            print(modification_for_instances_response)

        else:
            rds_client = common.assume_role(service='rds', role_arn=response['arn'], region=response['region'])

            for rds_item in rds_client.describe_db_instances().get('DBInstances', []):
                if request[item] == rds_item['DBInstanceIdentifier']:
                    db_arn = rds_item['DBInstanceArn']

                    if backup_values[0][backup_value] == True:
                        response = rds_client.add_tags_to_resource(
                            ResourceName=db_arn,
                            Tags=[modified_tag]
                        )
                    else:
                        response = rds_client.remove_tags_from_resource(
                            ResourceName=db_arn,
                            TagKeys=[
                                'AWSSchedule'
                            ]
                        )



