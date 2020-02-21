import os

import boto3
from boto3.dynamodb.conditions import Key

from . import common

from app.fn_get_client import get_client
from app.fn_set_current_refresh_date import set_current_refresh_date


def lambda_handler(event, context):
    config_db_name = common.get_table(os.environ['db'], 'ConfigTable')
    instance_table_name = os.environ['instancesDB']
    instances_table = boto3.resource("dynamodb").Table(instance_table_name)
    ec2_keys = os.environ['ec2keys'].split(',')

    set_current_refresh_date(
        config_db_name=config_db_name,
        item_type='instances'
    )

    instance_table_response = instances_table.scan(
        TableName=instance_table_name
    )['Items']

    client_items = get_client(os.environ['accountsDB'], 'ec2')

    instances_ids = []

    for client in client_items:
        ec2_client = client['service']

        instances = {}
        instances_items = {}
        items = []

        for ec2 in ec2_client.describe_instances().get( 'Reservations', [] ):
            for ec2_item in ec2['Instances']:
                if not 'terminated' in ec2_item['State']['Name']:
                    items.append(ec2_item)
                    instances_ids.append(ec2_item['InstanceId'])

        for item in items:
            for key in ec2_keys:
                instances_items[key] = item[key]
                instances[item['InstanceId']] = instances_items

            data = {
                "instanceId": item['InstanceId'],
                "accountId": client['account_id'],
                "accountAlias": client['account_alias'],
                'region': client['region'],
                'arn': client['arn']
            }

            for item_key in ec2_keys:
                data[item_key] = instances_items[item_key]

            instances_table.put_item(
                TableName=os.environ['instancesDB'],
                Item=data
            )

    for instance in instance_table_response:
        if instance['instanceId'] not in instances_ids:
            instances_table.delete_item(
                Key={
                    "instanceId": instance['instanceId']
                }
            )
    return common.return_response(body={'post': 'success'})