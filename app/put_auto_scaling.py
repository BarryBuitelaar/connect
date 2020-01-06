import boto3;
import os;
import json;

from boto3.dynamodb.conditions import Key;

from . import common

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable');
    config_table = boto3.resource("dynamodb").Table(dynamo_DB);
    instances_table = boto3.resource("dynamodb").Table(os.environ['asgDB']);
    asg_keys = os.environ['asgkeys'].split(',');

    autoscaling_group_names = [];
    asg_groups = {};
    asg_items = {};
    ec2_obj = {};

    client = boto3.client('ec2');

    response = config_table.query(
        TableName=dynamo_DB,
        KeyConditionExpression=Key("type").eq('config'),
    )

    items = response['Items'][0];
    roles = items['cross_account_roles'];

    for RoleArn in roles:
        autoscaling_client = common.assume_role('autoscaling', RoleArn, os.environ['region']);

        all_asgs = [];
        describe_auto_scaling_groups_paginator = autoscaling_client.get_paginator('describe_auto_scaling_groups');
        describe_auto_scaling_groups_iterator = describe_auto_scaling_groups_paginator.paginate();
        for describe_auto_scaling_groups_response in describe_auto_scaling_groups_iterator:
            all_asgs.extend(describe_auto_scaling_groups_response['AutoScalingGroups']);

        for group in all_asgs:
          autoscaling_group_names.append(group['AutoScalingGroupName']);
        
        for name in autoscaling_group_names:
            for key in asg_keys:
                asg_items[key] = group[key];

                asg_groups[name] = asg_items;

        for key in asg_groups.keys():
            data = {
                "asgName": key
            }

            for item_key in asg_groups[key].keys():
                data[item_key] = asg_groups[key][item_key];

            instances_table.put_item(
                TableName=os.environ['asgDB'],
                Item=data
            );
