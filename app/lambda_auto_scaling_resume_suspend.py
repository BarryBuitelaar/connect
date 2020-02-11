import boto3
import os
import json

from datetime import datetime, timedelta

from boto3.dynamodb.conditions import Key

from . import common
from app.fn_get_pas_helper import get_pas

from app.fn_auto_scaling_resume import auto_scaling_resume
from app.fn_auto_scaling_suspend import auto_scaling_suspend

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable')
    config_table = boto3.resource("dynamodb").Table(dynamo_DB)

    current_time = (datetime.now() + timedelta(hours=1)).strftime('%H:%M')
    current_weekday = datetime.now().isoweekday()

    days_of_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    autoscaling_group_names = []

    response = config_table.query(
        TableName=dynamo_DB,
        KeyConditionExpression=Key("type").eq('config'),
    )

    items = response['Items'][0]
    roles = items['cross_account_roles']

    pas = {}

    for data_type in ['period', 'schedule']:
        pas[data_type] = get_pas(config_table, dynamo_DB, data_type)

    schedule_names = []
    supply_asg = []

    for item in pas['schedule']:
        period = item['periods'] if 'periods' in item else None

        if period:
            new_dict = dict()
            for p in period:
                for period_item in pas['period']:
                    if p in period_item['name']:
                        new_dict[item['name']] = period_item
                        schedule_names.append(new_dict)

    for RoleArn in roles:
        autoscaling_client = common.assume_role('autoscaling', RoleArn, os.environ['region'])

        all_asgs = []
        describe_auto_scaling_groups_paginator = autoscaling_client.get_paginator('describe_auto_scaling_groups')
        describe_auto_scaling_groups_iterator = describe_auto_scaling_groups_paginator.paginate()
        for describe_auto_scaling_groups_response in describe_auto_scaling_groups_iterator:
            all_asgs.extend(describe_auto_scaling_groups_response['AutoScalingGroups'])

        for group in all_asgs:
          autoscaling_group_names.append(group['AutoScalingGroupName'])

          for tag in group['Tags']:
              for schedule in schedule_names:
                    for key in schedule.keys():
                        if key in tag['Key']:
                            if tag['Value'] == 'True':
                                new_asg_dict = dict()
                                new_asg_dict[tag['ResourceId']] = schedule[key]
                                new_asg_dict[tag['ResourceId']]['Instances'] = group['Instances']
                                new_asg_dict[tag['ResourceId']]['Value'] = tag['Value']
                                new_asg_dict[tag['ResourceId']]['IsSuspended'] = len(group['SuspendedProcesses']) > 0
                                supply_asg.append(new_asg_dict)

        between_days = []
        resume_asg = []

        for sup in supply_asg:
            for key in sup:
                begin_time = sup[key]['begintime']
                end_time = sup[key]['endtime']
                week_days = sup[key]['weekdays']

                for day in week_days:
                    if day.find('-') > -1:
                        splitted_days = day.split('-')
                        last_day = splitted_days[(len(splitted_days) - 1)]
                        first_day_index = (days_of_week.index(splitted_days[0]) + 1)
                        last_day_index = (days_of_week.index(last_day) + 1)
                        if current_weekday >= first_day_index and current_weekday <= last_day_index:
                            between_days.append(True)
                        else:
                            between_days.append(False)
                    else:
                        day_index = (days_of_week.index(day) + 1)

                        if day_index == current_weekday:
                            between_days.append(True)
                        else:
                            between_days.append(False)

                if len(between_days) > 0:
                    resume = True in between_days and begin_time < current_time and end_time > current_time
                    if resume:
                        resume_asg.append(key)

                response_dict = {
                    "asg": key,
                    "arn": RoleArn,
                    "region": os.environ['region'],
                    "Instances": sup[key]['Instances']
                }

                if resume:
                    if sup[key]['IsSuspended']:
                        auto_scaling_resume(response_dict)

                else:
                    if key not in resume_asg:
                        if not sup[key]['IsSuspended']:
                            auto_scaling_suspend(response_dict)

