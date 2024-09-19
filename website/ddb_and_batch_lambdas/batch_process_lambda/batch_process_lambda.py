import boto3
import datetime
import json
import logging
import os
from boto3.dynamodb.conditions import Key, Attr

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    ddb_name = os.getenv("DDB_NAME")
    target_lambda = os.getenv("TARGET_TABROOM_SUMMARY_LAMBDA")
    today = datetime.datetime.now()
    # Walk through all the DDB entries that are not processed
    ddb_resource = boto3.resource(
        "dynamodb",
    )
    table = ddb_resource.Table(ddb_name)
    max_invocations = 5
    invocation_count = 0
    all_items = table.scan(FilterExpression=Attr("prompts_generated").eq(False))[
        "Items"
    ]
    logging.info(f"Found {len(all_items)} tournaments to process.")
    for item in all_items:
        data = item
        tournament_id = data["tourn_id"]
        tournament_name = data["tourn_name"]
        end_date = data["end_date"]
        end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        if today < end_datetime + datetime.timedelta(days=1):
            logging.info(
                f"Skipping tournament {tournament_name} ({tournament_id}) because results are likely not ready yet."
            )
            continue
        elif today - datetime.timedelta(days=7) > end_datetime:
            logging.info(
                f"Skipping tournament {tournament_name} ({tournament_id}) because results are not available, even a week after its end-date."
            )
            continue
        else:
            # Asynchronously invoke the Lambda function to process the tournament data
            logging.info(
                f"Invoking {target_lambda} for tournament {tournament_name} ({tournament_id})"
            )
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


if __name__ == "__main__":
    os.environ["DDB_NAME"] = "tabroom_tournaments"
    os.environ["TARGET_TABROOM_SUMMARY_LAMBDA"] = (
        "docker-selenium-lambda-tabroom-prod-main"
    )
    lambda_handler(None, None)
