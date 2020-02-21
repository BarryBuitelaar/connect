import os

import boto3
from boto3.dynamodb.conditions import Key

from . import common

from app.fn_get_client import get_client
from app.fn_set_current_refresh_date import set_current_refresh_date


def lambda_handler(event, context):
    config_db_name = common.get_table(os.environ['db'], 'ConfigTable')
    rds_table = boto3.resource("dynamodb").Table(os.environ['rdsDB'])
    client_items = get_client(os.environ['accountsDB'], 'rds')

    set_current_refresh_date(
        config_db_name=config_db_name,
        item_type='rds'
    )

    for client in client_items:
        rds_client = client['service']

        for rds_item in rds_client.describe_db_instances().get('DBInstances', []):
            rds_tags = rds_client.list_tags_for_resource(
                ResourceName=rds_item['DBInstanceArn']
            )

            data = {
                'rdsName': rds_item['DBInstanceIdentifier'],
                'Tags': rds_tags['TagList'],
                "accountId": client['account_id'],
                "accountAlias": client['account_alias'],
                'region': client['region'],
                'arn': client['arn'],
                'state': rds_item['DBInstanceStatus']
            }

            rds_table.put_item(
                Item=data
            )

    return common.return_response(body={'post': 'success'})