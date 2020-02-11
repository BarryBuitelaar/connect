import boto3
import os

from . import common


def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable')
    table = boto3.resource("dynamodb").Table(dynamo_DB)

    request = common.json_body_as_dict(event)

    data = {
        "type": request['type'],
        "name": request['name'],
        "description": request['description']
    }

    if "description" in request:
        data['description'] = request['description']

    if "period" in request['type']:
        data.update(add_period(request))
    else:
        data.update(add_schedule(request))

    table.put_item(
        TableName=dynamo_DB,
        Item=data
    )

    return common.return_response(body={'post': 'success'})


def add_period(request):
    data = {
        'weekdays': request['weekdays']
    }

    if "endtime" in request:
        data['endtime'] = request['endtime']

    if "begintime" in request:
        data['begintime'] = request['begintime']

    return data


def add_schedule(request):
    data = {
        "periods": request['periods'],
        "backup": request['backup'],
        "timezone": request['timezone']
    }

    return data