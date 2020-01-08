import boto3
import os

from boto3.dynamodb.conditions import Key

from . import common
from app.get_instances_helper import lambda_handler as get_instances

def lambda_handler(event, context):
    return get_instances(event, os.environ['instancesDB'])
