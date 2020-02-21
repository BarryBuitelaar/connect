from datetime import datetime, timedelta

import boto3


def set_current_refresh_date(config_db_name, item_type):
    config_table = boto3.resource("dynamodb").Table(config_db_name)

    current_time = (datetime.now() + timedelta(hours=1)).strftime('%H:%M')
    weekday_index = datetime.now().isoweekday() - 1
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saterday', 'Sunday']
    current_date_in_string = F'{days_of_week[weekday_index]}: {current_time}'

    item = {
      "type": 'refreshDate',
      "name": item_type,
      "date": current_date_in_string
    }

    config_table.put_item(
      TableName=config_db_name,
      Item=item
    )



