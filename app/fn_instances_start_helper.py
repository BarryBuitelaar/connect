#!usr/bin/python
import logging

import boto3
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def start_instances(event, context):
    '''
    Single instance:
        - Instances
        - arn
        - region
    ASG:
        - asgName
        - Instances
        - arn
        - region
    '''

    request = common.json_body_as_dict(event)

    arn = request['arn']
    region = request['region']

    ec2 = common.assume_role('ec2', arn, region)
    auto_scaling_client = common.assume_role('autoscaling', arn, region)

    instance_ids = request['instances']

    t = type(instance_ids) == list

    try:
        ec2.start_instances(
            InstanceIds=[instance_ids] if not t else instance_ids,
        )
    except ClientError as e:
        return common.throw_error(F'Failed to start instance- Error: {e}')

    if t:
        try:
            auto_scaling_client.resume_processes(AutoScalingGroupName=request['asgName'])
        except ClientError as e:
            return common.throw_error(F'Failed to resume {request["asgName"]} - Error: {e}')

    return common.return_response(body={'post_success': 'started instances {instance_ids}'})