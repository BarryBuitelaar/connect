import boto3
import os
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from . import common
from app.fn_modify_asg_tags import modify_asg_tags

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable')
    instances_db_name = os.environ['instancesDB']
    asg_db_name = os.environ['asgDB']

    table = boto3.resource("dynamodb").Table(dynamo_DB)

    request = common.json_body_as_dict(event)

    if request['type'] == 'period':
        config_table_response = table.scan(
              TableName=dynamo_DB
        )

        for t in config_table_response['Items']:
            if t['type'] == 'schedule':
                if request['name'] in t['periods']:
                    return common.throw_error(F"Failed to delete period: {request['name']}. - This period is assinged to schedule: {t['name']}.")

        try:
            table.delete_item(
                Key={
                    'type': request['type'],
                    'name': request['name']
                }
            )
        except ClientError as e:
            return common.throw_error(F"Failed to delete period: {request['name']}. - {e}")

        return common.return_response(body={'post': 'success'})
    else:
        if 'itemsObject' in request:
            items = request['itemsObject']
            item_object = {}
            item_values = {}
            all_items_to_modify = []

            for region in items:
                item_object[region] = dict()
                for item in items[region]:
                    item_values[item] = []
                    if item in item_values: 
                        item_values[item].append(items[region][item])

                for arn in item_values:
                    item_object[region][arn] = {}
                    if len(item_values[arn]) > 0:
                        for t in item_values[arn]:
                            for k, val in t.items():
                                item_object[region][arn][val] = [k for k, v in t.items() if v == val]

            for region in item_object:
                for item_type in item_object[region]:
                    for arn in item_object[region][item_type]:
                        new_request = {
                            'selectedAccount': {
                                'arn': arn,
                                'region': region
                            },
                            'TagKey': request['name']
                        }
                        new_request[item_type] = list(map(lambda x : {x: True}, item_object[region][item_type][arn]))
                        all_items_to_modify.append(new_request)

            for new_request in [i for n, i in enumerate(all_items_to_modify) if i not in all_items_to_modify[n + 1:]]:
                tags = {
                    'Key': 'AWSSchedule',
                    'Value': request['name']
                }
                modify_asg_tags(request=new_request, instances_db_name=instances_db_name, asg_db_name=asg_db_name, instance_tag=tags, delete=True)

        try:
            table.delete_item(
                Key={
                    'type': request['type'],
                    'name': request['name']
                }
            )
        except ClientError as e:
            return common.throw_error(F"Failed to delete schedule: {request['name']}. - {e}")

    return common.return_response(body={'post': 'success'})
