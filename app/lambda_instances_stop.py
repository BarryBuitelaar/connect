import logging

import boto3
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def _lambda_handler(event, context):
    """
    Single instance:
        - Instances
        - arn
        - region
    ASG:
        - asgName
        - Instances
        - arn
        - region
    """
    request = common.json_body_as_dict(event)

    arn = request["arn"]
    region = request['region']

    ec2 = common.assume_role('ec2', arn, region)
    auto_scaling_client = common.assume_role('autoscaling', arn, region)

    instance_ids = request["instances"]

    t = type(instance_ids) == list

    try:
        ec2.stop_instances(
            InstanceIds=[instance_ids] if not t else instance_ids
        )
    except ClientError as e:
        return common.throw_error(F"Failed to stop instances - Error: {e}")

    if t:
        try:
            auto_scaling_client.suspend_processes(AutoScalingGroupName=request["asgName"])
        except ClientError as e:
            return common.throw_error(F"Failed to suspend {request['asgName']} - Error: {e}")

    return common.return_response(body={"post_success": 'stopped instances {instance_ids}'})


def lambda_handler(event, context):
    return common.lambda_handler(file=__file__, event=event, context=context, delegate=_lambda_handler)