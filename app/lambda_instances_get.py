import os

import boto3
from boto3.dynamodb.conditions import Key

from . import common
from app.fn_get_instances_helper import get_instances

def lambda_handler(event, context):
    return get_instances(event, os.environ['instancesDB'])
