import boto3;
import os;

from . import common

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable');
    table = boto3.resource("dynamodb").Table(dynamo_DB);

    request = common.json_body_as_dict(event);


    print('get')