# Synchronously invokes the LLM Lambda and emails the results to the provided email

import boto3
import json


def lambda_handler(event, context):
    email = event.get("email", None)
    tournament_id = event.get("tournament", None)
    school = event.get("school", None)
    if not email or not tournament_id or not school:
        raise Exception("Missing email, school, or tournament ID")
    # Invoke Lambda to process input using LLM
    lambda_client = boto3.client("lambda")
    response = lambda_client.invoke(
        FunctionName="api_lambda_function",
        InvocationType="RequestResponse",  # synchronous
        Payload=f'{{"tournament": "{tournament_id}", "school": "{school}"}}',
    )
    response_payload = response["Payload"].read().decode("utf-8")
    if "ERROR" in response_payload:
        raise Exception(response_payload)
    # Send email
    ses_client = boto3.client("ses")
    response = ses_client.send_email(
        Destination={"ToAddresses": [email]},
        Message={
            "Body": {
                "Text": {
                    "Charset": "UTF-8",
                    "Data": response_payload,
                }
            },
            "Subject": {
                "Charset": "UTF-8",
                "Data": f"Your Requested TabroomSummary.com Results - School {school} - Tournament {tournament_id}",
            },
        },
        Source="benjamin.morris@ucla.edu",
    )
    return {
        "statusCode": 200,
        "body": json.dumps(
            "Email Sent Successfully. MessageId is: " + response["MessageId"]
        ),
    }
