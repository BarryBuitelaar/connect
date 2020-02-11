import datetime, boto3, os, json, logging, time, traceback
from botocore.exceptions import ClientError
import datetime, sys

from boto3.dynamodb.conditions import Key

from . import common

from app.fn_get_client import get_client

# Set the log format
logger = logging.getLogger()
for h in logger.handlers:
    logger.removeHandler(h)

h = logging.StreamHandler(sys.stdout)
FORMAT = ' [%(levelname)s]/%(asctime)s/%(name)s - %(message)s'
h.setFormatter(logging.Formatter(FORMAT))
logger.addHandler(h)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    dynamo_DB = common.get_table(os.environ['db'], 'ConfigTable')
    config_table = boto3.resource("dynamodb").Table(dynamo_DB)
    # backup_table = boto3.resource("dynamodb").Table(os.environ['backupDB'])

    config_table_response = config_table.query(
        TableName=dynamo_DB,
        KeyConditionExpression=Key("type").eq('config'),
    )

    config_table_items = config_table_response['Items'][0]
    roles = config_table_items['cross_account_roles']

    for RoleArn in roles:
        backup_plan_client = common.assume_role('backup', RoleArn, os.environ['region'])

        backup_plans = []

        response = backup_plan_client.list_backup_plans()
        backup_plans_list = response['BackupPlansList']

        backup_plans_id_list = map(lambda el: el["BackupPlanId"], backup_plans_list)

        # retrieve and store all backup plans
        for backup_plan_id in backup_plans_id_list:
            # get backup_plan with backup_plan_id as id
            backup_plan = backup_plan_client.get_backup_plan(
                BackupPlanId=backup_plan_id
            )
            # get selections for backup_plan_id
            backup_selections = backup_plan_client.list_backup_selections(
                BackupPlanId=backup_plan_id
            )["BackupSelectionsList"]
            backup_selections_ids = map(lambda el: el["SelectionId"], backup_selections)

            backup_selections = []
            # get all selections
            for backup_selection_id in backup_selections_ids:
                backup_selection = backup_plan_client.get_backup_selection(
                    BackupPlanId=backup_plan_id,
                    SelectionId=backup_selection_id
                )
                backup_selections.append(backup_selection)
            backup_plan["selections"] = backup_selections
            backup_plans.append(backup_plan)
            
        # Ignores responseMetaData-fields
        # backup_plans = list(map(el: el['BackupPlan'], backup_plans))

        print(backup_plans)
