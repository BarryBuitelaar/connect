import boto3
import os

from boto3.dynamodb.conditions import Key

from . import common
from app.modify_tags import modify_tags

def lambda_handler(event, database_name, backup_values):
    instances_table = boto3.resource("dynamodb").Table(database_name)
    instance = event[0]

    response = instances_table.get_item(Key={
        'instanceId': instance['instanceId']
    })['Item']

    response = modify_tags(response, backup_values, False)

    instances_table.put_item(Item=response, ReturnValues='NONE')
