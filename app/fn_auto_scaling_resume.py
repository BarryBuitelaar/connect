import time, logging

import boto3
from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger(common.logger_name(__file__))


def auto_scaling_resume(event):
    request = common.json_body_as_dict(event)

    arn = request['arn']
    region = request['region']

    ec2_client = common.assume_role('ec2', arn, region)
    autoscaling_client = common.assume_role('autoscaling', arn, region)
    
    asg_name = request['asg']
    instances = request['Instances']

    # start instances
    if instances:
        instance_ids = [i["InstanceId"] for i in instances]

        try:
            ec2_client.start_instances(InstanceIds=instance_ids)
            logger.info(F'Started your instances: {instance_ids}')
        except ClientError as e:
            return common.throw_error(F'Could not start instances for group {asg_name}: {e}')
    else:
        logger.info(F'No instances found in group {asg_name}')

    logger.info('15 sec pause before resume')
    time.sleep(15)

    # resume the asg group
    try:
        response = autoscaling_client.resume_processes(AutoScalingGroupName=asg_name)
        logger.info(F'{asg_name} is resumed')
    except ClientError as e:
        return common.throw_error(F'Could not resume ASG {asg_name}: {e}')

    return common.return_response(body={
        'post_success': F'{asg_name} is resumed, {len(instances)} started'
    })
