import boto3
import os

from boto3.dynamodb.conditions import Key

from . import common

def get_instances(event, database_name):
    instances_table = boto3.resource("dynamodb").Table(database_name)

    if 'InstanceId' in event.keys():
        response = instances_table.query(
            TableName=database_name,
            KeyConditionExpression=Key("instanceId").eq(event['InstanceId']),
        )
        return(response['Items'])
    else:
        response = instances_table.scan(
            TableName=database_name
        )

        for res in response['Items']:
            res['State']['Code'] = int(res['State']['Code'])

        return common.return_response(body=response['Items'])
