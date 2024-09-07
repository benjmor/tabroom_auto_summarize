import boto3
import datetime
import json
import logging

REGION = "us-east-1"
ddb_name = "tabroom_tournaments"

today = datetime.datetime.now()
# Walk through all the DDB entries that are not processed
ddb_resource = boto3.resource(
    "dynamodb",
    region_name=REGION,
)
table = ddb_resource.Table(ddb_name)
scan_filter = {
    "FilterExpression": "prompts_generated = :value",
    "ExpressionAttributeValues": {":value": {"BOOL": False}},
}
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
    lambda_client = boto3.client("lambda", region_name=REGION)
    lambda_client.invoke(
        FunctionName="docker-selenium-lambda-tabroom-prod-main",
        InvocationType="Event",
        Payload=json.dumps(
            {
                "tournament": tournament_id,
                "school": "None/Batch-Requested",
            }
        ),
    )
    # Waiting here would time out, so make sure that the processing lambdas mark the records as True in DDB
