import boto3
import os
from tabroom_summary import tabroom_summary


def lambda_handler(event, context):
    # This function will query Tabroom.com for the tournament results and then
    # return a summary of the results using ChatGPT.
    tournament_id = event["tournament"]
    open_ai_key_path = event.get("open_ai_key_path")
    response = tabroom_summary.main(
        all_schools=True, tournament_id=tournament_id, open_ai_key_path=open_ai_key_path
    )
    if event["debug"]:
        return response
    # Save the tournament results to S3
    s3_client = boto3.client("s3")
    bucket_name = os.environ["DATA_BUCKET_NAME"]
    for school_name in response.keys():
        s3_client.put_object(
            Body=response["gpt_response"],
            Bucket=bucket_name,
            Key=f"{tournament_id}/{school_name}/results.txt",
        )
        s3_client.put_object(
            Body=response["gpt_prompt"],
            Bucket=bucket_name,
            Key=f"{tournament_id}/{school_name}/gpt_prompt.txt",
        )


if __name__ == "__main__":
    debug = True
    event = {
        "tournament": "20134",
        "debug": True,
        "open_ai_key_path": "./tabroom_summary/openAiAuthKey.txt",
    }
    lambda_handler(event, {})
