from . import common
from app.fn_instances_stop_helper import stop_instances


def lambda_handler(event, context):
    return common.lambda_handler(file=__file__, event=event, context=context, delegate=stop_instances)
