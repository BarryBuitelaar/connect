import boto3
import os
import json

from boto3.dynamodb.conditions import Key

from . import common

from app.fn_get_client import get_client

def lambda_handler(event, context):
    rds_table = boto3.resource("dynamodb").Table(os.environ['rdsDB'])
    rds_client = get_client(os.environ['db'], 'rds', os.environ['region'])

    for rds_item in rds_client.describe_db_instances().get('DBInstances', []):
        rds_tags = rds_client.list_tags_for_resource(
            ResourceName=rds_item['DBInstanceArn']
        )

        data = {
            'rdsName': rds_item['DBInstanceIdentifier'],
            'Tags': rds_tags['TagList']
        }

        rds_table.put_item(
            Item=data
        )