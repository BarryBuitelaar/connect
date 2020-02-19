import json
import boto3
import logging
import random
import traceback
from os import environ
from typing import Union, Callable, List
from datetime import datetime
import re

# logger = logging.getLogger()

_REGEX_SEPARATOR = re.compile("[/\\\\]")


def logger_name(file_name):
    return _REGEX_SEPARATOR.split(file_name)[-1][:-3]


logger = logging.getLogger(logger_name(__file__))

log_base_name = None

def get_table(prefix, suffix):
    database = boto3.resource('dynamodb')

    table_names = [table.name for table in database.tables.all()]

    table_name = F"{prefix}-{suffix}"

    for table in table_names:
        if table_name in table:
            return table
        else:
            print(F"Table: {table_name} not found")
            return None


def assume_role(service, role_arn, region):
    sts_client = boto3.client('sts')
    assumed_role_object=sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName="AssumeRoleSession1"
    )
    credentials=assumed_role_object['Credentials']
    service_client=boto3.client(
        service,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken'],
        region_name=region
    )

    return service_client


class Json(object):
    @staticmethod
    def pretty(obj):
        return json.dumps(obj=obj, indent=2, default=Json._default)

    @staticmethod
    def compact(obj):
        return json.dumps(obj=obj)

    @staticmethod
    def _default(obj):
        return obj.__dict__ if '__dict__' in dir(obj) else "{}".format(obj)


def json_body_as_dict(event):
    if "body" not in event:
        return None
    else:
        return json.loads(event["body"])



def return_response(body: dict):
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "body": Json.compact(body),
    }
    return response


def throw_error(message):
    global logger

    logger.error(message)
    return return_response(body={
        "post_error": message
    })

def handle_error():
    trace = traceback.format_exc()
    error_id = "{:%Y-%m-%d %H:%M:%S}-{}".format(datetime.now(), random.randint(1000, 9999))
    logger.error("An uncaught exception occurred. Error ID %s. Detail %s", error_id, trace)

    return return_response(
        body={"Error": "Oops something went wrong. Error ID \"{}\"".format(error_id)}
    )

def config_logging_to_aws():
    formatter = logging.Formatter(
        fmt="{asctime} [{levelname}] '{name}' - {message}",
        style="{",
        datefmt="%Y-%m-%dT%H:%M:%S.%fZ",
    )
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            handler.setFormatter(formatter)

    inqdo_logger = logging.getLogger("inqdo")
    if "LogLevel" in environ:
        inqdo_logger.setLevel(environ["LogLevel"])
    else:
        inqdo_logger.setLevel(logging.INFO)

def lambda_handler(file: str, event, context, delegate: Callable):
    config_logging_to_aws()
    # noinspection PyBroadException
    try:
        response = delegate(event=event, context=context)
    except Exception:
        return handle_error()
    return response