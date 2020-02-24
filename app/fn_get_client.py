import boto3
from boto3.dynamodb.conditions import Key

from . import common

def get_client(account_db, service):
  account_table = boto3.resource("dynamodb").Table(account_db)

  account_table_response = account_table.scan(
      TableName=account_db
  )['Items']

  response = []

  for account in account_table_response:
    account_alias = account['accountAlias']
    region = account['region']
    account_id = account['accountId']
    arn = account['arn']

    service_client = common.assume_role(service, arn, region)

    response.append({
      'service': service_client,
      'account_id': account_id,
      'account_alias': account_alias,
      'region': region,
      'arn': arn
    })

  return response