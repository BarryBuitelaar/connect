import boto3
import os

from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from . import common
from app.fn_instances_stop_helper import stop_instances

def lambda_handler(event, context):
    request = common.json_body_as_dict(event)
    instances_db_name = os.environ['instancesDB']
    asg_db_name = os.environ['asgDB']

    instances_table = boto3.resource("dynamodb").Table(instances_db_name)
    asg_table = boto3.resource("dynamodb").Table(asg_db_name)

    current_time = (datetime.now() + timedelta(hours=1)).strftime('%H:%M')

    asg_table_response = asg_table.scan(
        TableName=os.environ['asgDB']
    )['Items']

    instances_table_response = asg_table.scan(
        TableName=os.environ['instancesDB']
    )['Items']

    asg_list = list(filter(lambda x: x != False, [
        (
            asg['asgName'],
            list(map(lambda el: el['InstanceId'], asg['Instances'])),
            asg['arn'], asg['region']
        ) if tag['Key'] == 'power-off-daily' else False
        for asg in asg_table_response
        for tag in asg['Tags']
    ]))


    instance_list = list(filter(lambda x: x != False, [
        (
            instance['instanceId'],
            tag['Value'], instance['arn'],
            instance['region']
        ) if tag['Key'] == 'power-off-daily' else False
        for instance in instances_table_response
        for tag in instance['Tags']
    ]))

    instances_to_stop = []
    asgs_to_stop = []

    if len(asg_list) > 0:
        for asg_tuple in asg_list:
            asg_name, asg_instances, asg_arn, asg_region = asg_tuple

            for instance_tuple in instance_list:
                instance_id, instance_time = instance_tuple

                if (instance_time <= current_time) and (instance_id in asg_instances):
                    asgs_to_stop.append({
                        "time": instance_time,
                        "asg_name": asg_name,
                        "instances": asg_instances,
                        "arn": asg_arn,
                        "region": asg_region
                    })
                    instance_list.pop(instance_list.index((instance_id, instance_time, asg_arn, asg_region)))


    if len(instance_list) > 0:
        for t in instance_list:
            instance_id, time, instance_arn, instance_region = t

            if time <= current_time:
                instances_to_stop.append({
                    "instances": instance_id,
                    "arn": instance_arn,
                    "region": instance_region
                })


    if len(instances_to_stop) > 0:
        for instance_request in instances_to_stop:
            stop_instances(instance_request, False)

    if len(asgs_to_stop) > 0:
        for asg in asgs_to_stop:
            request = {
                'asgName': asg['asg_name'],
                'instances': asg['instances'],
                'arn': asg['arn'],
                'region': asg['region']
            }
            stop_instances(request, False)