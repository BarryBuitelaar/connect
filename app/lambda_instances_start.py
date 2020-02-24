import logging

import boto3
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    '''
    required parameters:
        start single instance:
            - instance
            - arn
            - region
        ASG:
            - asgName # if present: resume ASG process
            - instances
            - arn
            - region
    '''
    request = common.json_body_as_dict(event)

    arn = request['arn']
    region = request['region']

    ec2 = common.assume_role('ec2', arn, region)
    auto_scaling_client = common.assume_role('autoscaling', arn, region)

    if 'instances' in request:
        instance_ids = request['instances']
    else:
        instance_ids = [request['instance']] # if a single instance is provided, wrap in list

    try:
        ec2.start_instances(InstanceIds=instance_ids)
    except ClientError as e:
        return common.throw_error(F'Failed to start instance: {e}')

    if 'asgName' in request:
        try:
            auto_scaling_client.resume_processes(AutoScalingGroupName=request['asgName'])
        except ClientError as e:
            return common.throw_error(F'Failed to resume {request["asgName"]}: {e}')

    return common.return_response(body={'post_success': F'started instances {instance_ids}'})
