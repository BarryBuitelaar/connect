import boto3
import os
import json

from boto3.dynamodb.conditions import Key

from . import common

from app.fn_get_client import get_client

def lambda_handler(event, context):
    asg_table_name = os.environ['asgDB']
    asg_table = boto3.resource("dynamodb").Table(asg_table_name)
    asg_keys = os.environ['asgkeys'].split(',')
    
    asg_table_response = asg_table.scan(
        TableName=asg_table_name
    )['Items']

    client_items = get_client(os.environ['accountsDB'], 'autoscaling')
    
    all_auto_scaling_groups = []

    for client in client_items:
        asg_groups = []
        asg_items = {}

        autoscaling_client = client['service']

        all_asgs = []
        describe_auto_scaling_groups_paginator = autoscaling_client.get_paginator('describe_auto_scaling_groups')
        describe_auto_scaling_groups_iterator = describe_auto_scaling_groups_paginator.paginate()
        for describe_auto_scaling_groups_response in describe_auto_scaling_groups_iterator:
            all_asgs.extend(describe_auto_scaling_groups_response['AutoScalingGroups'])

        for group in all_asgs:
            group_name = group['AutoScalingGroupName']
            asg_group_dict = dict()
            asg_items = dict()

            all_auto_scaling_groups.append(group_name)
            for key in asg_keys:
                asg_items[key] = group[key]
                asg_group_dict[group_name] = asg_items
            
            asg_groups.append(asg_group_dict)

        for asg_group in asg_groups:
            for key in asg_group.keys():
                data = {
                    "asgName": key,
                    "accountId": client['account_id'],
                    "accountAlias": client['account_alias'],
                    'region': client['region'],
                    'arn': client['arn']
                }

                for item_key in asg_group[key].keys():
                    data[item_key] = asg_group[key][item_key]

                asg_table.put_item(
                    TableName=os.environ['asgDB'],
                    Item=data
                )
                

        for asg in asg_table_response:
            if asg['asgName'] not in all_auto_scaling_groups:
                asg_table.delete_item(
                    Key={
                        "asgName": asg['asgName']
                    }
                )
