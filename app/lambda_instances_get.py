import os

from app.fn_get_instances_helper import get_instances

def lambda_handler(event, context):
    return get_instances(event, os.environ['instancesDB'])
