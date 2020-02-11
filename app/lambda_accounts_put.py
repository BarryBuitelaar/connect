import boto3
import os
import json

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from . import common

def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable')
    config_table = boto3.resource("dynamodb").Table(dynamo_DB)
    accounts_table = boto3.resource("dynamodb").Table(os.environ['accountDB'])

    response = config_table.query(
        TableName=dynamo_DB,
        KeyConditionExpression=Key("type").eq('config'),
    )

    items = response['Items'][0]
    roles = items['cross_account_roles']
    regions = items['regions']

    for RoleArn in roles:
        AccountId = RoleArn.split(":")[4]

        for region in regions:
            iam_client = common.assume_role('iam', RoleArn, region)
            try:
                accounts_table.put_item(
                    Item={
                    "accountId": AccountId,
                    "arn": RoleArn,
                    "accountAlias": iam_client.list_account_aliases()['AccountAliases'][0],
                    "region": region,
                    "backupDefaultServiceRole": f"arn:aws:iam::{AccountId}:role/service-role/AWSBackupDefaultServiceRole"
                    }
                )
            except ClientError as e:
                common.throw_error(F"Failed add account information: {AccountId} = {e}")