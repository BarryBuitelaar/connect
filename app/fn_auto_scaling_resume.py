import datetime, boto3, os, json, logging, time, traceback
from botocore.exceptions import ClientError
import datetime, sys

# Set the log format
logger = logging.getLogger()
for h in logger.handlers:
    logger.removeHandler(h)

h = logging.StreamHandler(sys.stdout)
FORMAT = ' [%(levelname)s]/%(asctime)s/%(name)s - %(message)s'
h.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(h)
logger.setLevel(logging.INFO)

# noinspection PyUnusedLocal
def auto_scaling_resume(event):
    RoleArn = event['arn']
    region = event['region']
    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn= RoleArn,
        RoleSessionName="AssumeRoleSession1"
    )
    credentials=assumed_role_object['Credentials']
    ec2_client=boto3.client(
        'ec2',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name=region
    )
    autoscaling_client=boto3.client(
        'autoscaling',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name=region
    )
    asg_name = event['asg']
    instances = event['Instances']

    #Start instances
    if len(instances)==0:
        print(f"No instances found in group {asg_name}")
        # print(f"Therefore {asg_name} will not be resumed.")
        # to_resume_asgs.remove(to_resume_asg)
    else:
        instance_ids = [
            i["InstanceId"]
            for i in instances
        ]
        print(instance_ids)
        try:
            ec2_client.start_instances(InstanceIds=instance_ids)
            print('started your instances: ' + str(instance_ids))
        except ClientError as e:
            print(f"ERROR: Could not start instances for group {asg_name}: {e}")
            # print(f"Therefore {asg_name} will not be resumed.")
            # to_resume_asgs.remove(to_resume_asg)

    print ('wait for 15 seconds before resume autoscalinggroup')
    time.sleep(15)

    #Resume the asg Group
    try:
        response = autoscaling_client.resume_processes(AutoScalingGroupName=asg_name)
        print(response)
        print(asg_name + ' is resumed')
    except ClientError as e:
        print(f"ERROR: Could not resume {asg_name}: {e}")

    print('Finished all work.')