import logging, time

import boto3
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def auto_scaling_suspend(event):
    arn = event['arn']
    region = event['region']

    ec2_client = common.assume_role(service='ec2', role_arn=arn, region=region)
    autoscaling_client = common.assume_role(service='autoscaling', role_arn=arn, region=region)

    # suspend the asg group
    asg_name = event['asg']
    try:
        response = autoscaling_client.suspend_processes(AutoScalingGroupName=asg_name)
        logging.info(F'{asg_name} is successfully suspended')
    except ClientError as e:
        return common.throw_error(F'Failed to suspend ASG {asg_name}, instances will not be stopped: {e}')

    time.sleep(5)

    # stop instances
    instances = event['Instances']
    instance_ids = [
        i['InstanceId']
        for i in instances
    ]
    
    try:
        ec2_client.stop_instances(InstanceIds=instance_ids)
        logging.info(F'Stopped instances: {instance_ids}')
    except ClientError as e:
        return common.throw_error(F'Could not stop instances for group/ASG {asg_name}: {e}')
