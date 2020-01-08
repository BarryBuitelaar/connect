import boto3
import os
import json

from boto3.dynamodb.conditions import Key

from . import common

from app.get_instances import lambda_handler as get_instances
from app.modify_instances import lambda_handler as modify_instance
from app.modify_tags import modify_tags

def lambda_handler(event, context):
    asg_table = boto3.resource("dynamodb").Table(os.environ['asgDB'])
    asg_keys = os.environ['asgkeys'].split(',')
    instanceDB = os.environ['instancesDB']

    backup_values = []

    request = common.json_body_as_dict(event)

    response = asg_table.get_item(Key={
        'asgName': request['asgName']
    })['Item']

    all_instances = response['Instances']

    for key in request.keys():
        if key in asg_keys:
            new_dict = dict()
            new_dict[key] = request[key]
            backup_values.append(new_dict)
        else:
            print('nothning found')

    response = modify_tags(response, backup_values, True)

    asg_table.put_item(Item=response, ReturnValues='NONE')

    instance_ids = [{ k:v for k, v in d.items() if k == 'InstanceId'} for d in all_instances ]

    for item in instance_ids:
        instance = get_instances(item, instanceDB)['body']
        modify_instance(json.loads(instance), instanceDB, backup_values)

    return common.return_response(body={'post': 'success'})
