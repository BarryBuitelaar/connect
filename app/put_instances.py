import boto3;
import os;
import json;

from boto3.dynamodb.conditions import Key;

from . import common

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable');
    config_table = boto3.resource("dynamodb").Table(dynamo_DB);
    instances_table = boto3.resource("dynamodb").Table(os.environ['instancesDB']);
    ec2_keys = os.environ['ec2keys'].split(',');

    instances_ids = [];
    instances = {};
    instaces_items = {};
    ec2_obj = {};

    client = boto3.client('ec2');

    response = config_table.query(
        TableName=dynamo_DB,
        KeyConditionExpression=Key("type").eq('config'),
    )

    items = response['Items'][0];
    roles = items['cross_account_roles'];

    for RoleArn in roles:
        ec2_client = common.assume_role('ec2', RoleArn, os.environ['region']);

        for ec2 in ec2_client.describe_instances().get( 'Reservations', [] ):
            for item in ec2['Instances']:
                instances_ids.append(item['InstanceId']);

            for id in instances_ids:
                for key in ec2_keys:
                    instaces_items[key] = item[key];

                    instances[id] = instaces_items;

        for instance_id in instances.keys():
            data = {
                "instanceId": instance_id
            }

            for item_key in instances[instance_id].keys():
                data[item_key] = instances[instance_id][item_key];

            instances_table.put_item(
                TableName=os.environ['instancesDB'],
                Item=data
            );
