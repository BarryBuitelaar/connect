from . import common
<<<<<<< HEAD
from app.fn_instances_stop_helper import stop_instances


def lambda_handler(event, context):
    return common.lambda_handler(file=__file__, event=event, context=context, delegate=stop_instances)
=======

logger = logging.getLogger(common.logger_name(__file__))


def lambda_handler(event, context):
    '''
    see lambda_instances_start for interface
    '''
    request = common.json_body_as_dict(event)

    arn = request['arn']
    region = request['region']

    ec2_client = common.assume_role('ec2', arn, region)
    auto_scaling_client = common.assume_role('autoscaling', arn, region)

    if 'instances' in request:
        instance_ids = request['instances']
    else:
        instance_ids = [request['instance']]

    try:
        ec2_client.stop_instances(
            InstanceIds=instance_ids
        )
    except ClientError as e:
        return common.throw_error(F'Failed to stop instances: {e}')

    if 'asgName' in request:
        try:
            auto_scaling_client.suspend_processes(AutoScalingGroupName=request['asgName'])
        except ClientError as e:
            return common.throw_error(F'Failed to suspend {request["asgName"]}: {e}')

    return common.return_response(body={'post_success': F'stopped instances {instance_ids}'})
>>>>>>> 2925e82f5bad5baa58ead86a9efbb87e5cebbc12
