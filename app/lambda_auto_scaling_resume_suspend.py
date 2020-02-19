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
    asg_db_name = os.environ['asgDB']
    config_table = boto3.resource("dynamodb").Table(dynamo_DB)
    asg_table = boto3.resource("dynamodb").Table(asg_db_name)

    current_time = (datetime.now() + timedelta(hours=1)).strftime('%H:%M')
    current_weekday = datetime.now().isoweekday()

    days_of_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    asg_table_response = asg_table.scan(
        TableName=asg_db_name,
    )['Items']

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

    for group in asg_table_response:
          new_asg_dict = dict()
          for tag in group['Tags']:
                  for schedule in schedule_names:
                        for key in schedule.keys():
                            if key in tag['Key']:
                                if tag['Value'] == 'True':
                                    new_asg_dict[tag['ResourceId']] = {
                                        'begintime': schedule[key]['begintime'],
                                        'description': schedule[key]['description'],
                                        'endtime': schedule[key]['endtime'],
                                        'weekdays': schedule[key]['weekdays'],
                                        'name': schedule[key]['name'],
                                        'type': schedule[key]['type'],
                                        'Instances': group['Instances'],
                                        'Value': tag['Value'],
                                        'region': group['region'],
                                        'IsSuspended': len(group['SuspendedProcesses']) > 0,
                                        'arn': group['arn']
                                    }
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
                "arn": sup[key]['arn'],
                "region": sup[key]['region'],
                "Instances": sup[key]['Instances']
            }

            if resume:
                if sup[key]['IsSuspended']:
                    print('resume', response_dict)
                    auto_scaling_resume(response_dict)

            else:
                if key not in resume_asg:
                    if not sup[key]['IsSuspended']:
                        print('suspend', response_dict)
                        auto_scaling_suspend(response_dict)

