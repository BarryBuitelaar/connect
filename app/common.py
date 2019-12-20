import json;
import boto3;
import os;

def get_table(prefix, suffix):
    database = boto3.resource('dynamodb');

    table_names = [table.name for table in database.tables.all()];

    table_name = F"{prefix}-{suffix}";

    for table in table_names:
        if table_name in table:
            return table;
        else:
            print(F"Table: {table_name} not found");
            return None;

class Json(object):
    @staticmethod
    def pretty(obj):
        return json.dumps(obj=obj, indent=2, default=Json._default)

    @staticmethod
    def compact(obj):
        return json.dumps(obj=obj, default=Json._default)

    @staticmethod
    def _default(obj):
        return obj.__dict__ if '__dict__' in dir(obj) else "{}".format(obj)

def json_body_as_dict(event):
  if "body" not in event:
    return None
  else:
    return json.loads(event["body"])

def return_response(body: dict) -> dict:
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "body": Json.compact(body),
    }
    return response