import boto3
import os

from boto3.dynamodb.conditions import Key

from . import common

def get_pas(table, table_name, data_type):

    response = table.query(
        TableName=table_name,
        KeyConditionExpression=Key("type").eq(data_type),
    )

    return response['Items']
