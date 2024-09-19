import argparse
import boto3
import datetime
import logging
import os
import traceback
from tabroom_summary import tabroom_summary

"""
This is the main routine for the tabroom_summary Lambda. It will query Tabroom.com for the tournament results and then
create a PROMPT that can be passed to an LLM to generate a summary of a school's results at the tournament.

Unlike previous versions, this version will NOT ever directly send LLM prompts to an LLM. That behavior now occurs synchronously at user-request time.
"""

# Set log level
logging.basicConfig(level=logging.INFO)

DATA_BUCKET = "tabroom-summaries-data-bucket"  # TODO - remove after testing


def handler(event, context):
    try:
        running_outside_of_lambda = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None
        print(event)
        # Send ol' Benjamin an email to let him know that people are using the service
        try:
            boto3.client("sns").publish(
                TopicArn=os.environ["SNS_TOPIC_ARN"],
                Message=f"Running tabroom_summary for {event['tournament']}; requested school is {event['school']}",
            )
        except Exception:
            logging.error("Error publishing to SNS")

        # Generate a Tabroom summary
        tournament_id = event["tournament"]
        event_context = event.get("context", "")
        percentile_minimum = event.get("percentile_minimum", 25)
        response, tourn_metadata = tabroom_summary.main(
            tournament_id=tournament_id,
            data_bucket=os.getenv("DATA_BUCKET_NAME", DATA_BUCKET),
            context=event_context,
            percentile_minimum=percentile_minimum,
        )

        # Save the result outputs
        # If we're not in Lambda, assume we're in Windows
        if running_outside_of_lambda:
            # Make the directories as needed
            for school_name in response.keys():
                os.makedirs(f"{tournament_id}/{school_name}", exist_ok=True)
                if "gpt_prompt" in response[school_name]:
                    with open(
                        f"{tournament_id}/{school_name}/gpt_prompt.txt", "w"
                    ) as f:
                        f.write(response[school_name]["gpt_prompt"])
        else:
            # Save the tournament results to S3
            s3_client = boto3.client("s3")
            bucket_name = os.environ["DATA_BUCKET_NAME"]
            for school_name in response.keys():
                if "gpt_prompt" in response[school_name]:
                    s3_client.put_object(
                        Body=response[school_name]["gpt_prompt"],
                        Bucket=bucket_name,
                        Key=f"{tournament_id}/{school_name}/gpt_prompt.txt",
                    )
                if "numbered_list_prompt" in response[school_name]:
                    s3_client.put_object(
                        Body=response[school_name]["numbered_list_prompt"],
                        Bucket=bucket_name,
                        Key=f"{tournament_id}/{school_name}/numbered_list_prompt.txt",
                    )
            try:
                # Delete the placeholder to signal to the Lambda that execution is complete
                s3_client.delete_object(
                    Bucket=bucket_name, Key=f"{tournament_id}/placeholder.txt"
                )
            except Exception:
                pass
        # Find or update the DDB table with the values
        end_date = datetime.datetime.strptime(
            tourn_metadata.get("end"), "%Y-%m-%d %H:%M:%S"
        )
        end_date = end_date.strftime("%Y-%m-%d")
        data = {
            "tourn_id": {
                "S": tournament_id,
            },
            "tourn_name": {
                "S": tourn_metadata.get("name", ""),
            },
            "end_date": {
                "S": end_date,
            },
            "locality": {
                "S": tourn_metadata.get("state", "N/A"),
            },
            "prompts_generated": {
                "BOOL": True,
            },
        }
        ddb_client = boto3.client(
            "dynamodb",
            region_name="us-east-1",
        )
        table_name = "tabroom_tournaments"
        logging.info(f"Updating DDB table {table_name} with item {data}")
        response = ddb_client.put_item(
            TableName=table_name,
            Item=data,
        )
    except Exception as e:
        logging.error(f"Tabroom Summary failed with the following error! {repr(e)}!")
        if tournament_id:
            message = f"Tabroom Summary for tournament {tournament_id} failed with the following error! {repr(e)}! Traceback: {traceback.format_exc()}"
        else:
            message = f"Tabroom Summary failed with the following error! {repr(e)}! Traceback: {traceback.format_exc()}"
        try:
            boto3.client("sns").publish(
                TopicArn=os.environ["SNS_TOPIC_ARN"],
                Message=f"Tabroom Summary failed with the following error! {repr(e)}!",
            )
        except Exception:
            logging.error("Error publishing error to SNS")
    try:
        boto3.client("sns").publish(
            TopicArn=os.environ["SNS_TOPIC_ARN"],
            Message=f"Tabroom results successfully generated for tournament {tournament_id} ({tourn_metadata.get("name", "")})!",
        )
    except Exception:
        logging.info(f"Error publishing error to SNS. Tabroom results successfully generated for tournament {tournament_id} ({tourn_metadata.get("name", "")})!")


if __name__ == "__main__":
    os.environ["SNS_TOPIC_ARN"] = (
        "arn:aws:sns:us-east-1:238589881750:summary_generation_topic"
    )
    # Create an argparse for tournament ID and readonly
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--tournament-id",
        help="Tournament ID (typically a 5-digit number) of the tournament you want to generate results for.",
        required=False,  # TODO - require again
        default="28354",
    )
    args = parser.parse_args()
    tournament_id = args.tournament_id
    event = {
        "tournament": tournament_id,  # "30799",  # "29810",  # "20134",
        # "context": "This tournament is the California State Championship, which requires students to qualify to the tournament from their local region. Round 4 of Congress and speech events is the semifinal round. Round 5 of Congress and speech events is the final round. In debate events, there are 4 preliminary rounds, followed by elimination rounds. All rounds were judged by panels of judges who each evaluated competitors and submitted an independent ballot.",  # CHSSA-specific
        "percentile_minimum": 25,  # CHSSA championship -- should include all results
    }
    handler(event, {})
