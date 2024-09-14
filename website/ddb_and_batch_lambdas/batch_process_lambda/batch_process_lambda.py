import boto3
import datetime
import json
import logging
import os

ddb_name = "tabroom_tournaments"

def lambda_handler(event, context):
    ddb_name = os.getenv("DDB_NAME")
    target_lambda = os.getenv("TARGET_TABROOM_SUMMARY_LAMBDA")
    today = datetime.datetime.now()
    # Walk through all the DDB entries that are not processed
    ddb_resource = boto3.resource(
        "dynamodb",
    )
    table = ddb_resource.Table(ddb_name)
    scan_filter = {
        "FilterExpression": "prompts_generated = :value",
        "ExpressionAttributeValues": {":value": {"BOOL": False}},
    }
    max_invocations = 5
    invocation_count = 0
    all_items = table.scan(**scan_filter)["Items"]
    for item in all_items:
        data = item
        tournament_id = data["tourn_id"]
        tournament_name = data["tourn_name"]
        end_date = data["end_date"]
        end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        if today > end_datetime + datetime.timedelta(days=1):
            logging.info(
                f"Skipping tournament {tournament_name} ({tournament_id}) because results are likely not ready yet."
            )
            continue
        elif today + datetime.timedelta(days=7) < end_datetime:
            logging.info(
                f"Skipping tournament {tournament_name} ({tournament_id}) because results are not available, even a week after its end-date."
            )
            continue
        # Asynchronously invoke the Lambda function to process the tournament data
        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName=target_lambda,
            InvocationType="Event",
            Payload=json.dumps(
                {
                    "tournament": tournament_id,
                    "school": "None/Batch-Requested",
                }
            ),
        )
        # A little logic so that we're not slamming everything into this process at once
        invocation_count += 1
        if invocation_count >= max_invocations:
            break
        # Waiting here would time out, so make sure that the processing lambdas mark the records as True in DDB
