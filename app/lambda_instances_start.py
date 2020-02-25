from . import common
from app.fn_instances_start_helper import start_instances

def lambda_handler(event, context):
    return common.lambda_handler(file=__file__, event=event, context=context, delegate=start_instances)