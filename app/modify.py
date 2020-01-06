import boto3;
import os;
import json;

from . import common

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable');
    table = boto3.resource("dynamodb").Table(dynamo_DB);

    request = common.json_body_as_dict(event);

    response = table.get_item(Key={
        'type': request['type'],
        'name': request['name']
    });

    item = response['Item'];

    for key in request:
        item[key] = request[key];

    table.put_item(Item=item);

    return common.return_response(body={'post': 'success'});
