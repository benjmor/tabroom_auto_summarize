import boto3
import logging
import os
from tabroom_summary import tabroom_summary

# Set log level
logging.basicConfig(level=logging.INFO)


def handler(event, context):
    print(event)
    # This function will query Tabroom.com for the tournament results and then
    # return a summary of the results using ChatGPT.
    # This Lambda will run asynchronously and will not return the results directly.
    debug = event.get("debug", False)
    try:
        open_ai_key_secret_name = os.environ["OPEN_AI_KEY_SECRET_NAME"]
    except KeyError:
        open_ai_key_secret_name = "openai_auth_key"
    tournament_id = event["tournament"]
    if debug:
        # For debugging, we will run the function locally and return the results to the user
        response = tabroom_summary.main(
            all_schools=True,
            tournament_id=tournament_id,
            open_ai_key_path=event["open_ai_key_path"],
            debug=debug,
            read_only=event.get("read_only", False),
        )
    response = tabroom_summary.main(
        all_schools=True,
        tournament_id=tournament_id,
        open_ai_key_secret_name=open_ai_key_secret_name,
        debug=debug,
        read_only=event.get("read_only", False),
    )
    # If we're not in Lambda, assume we're in Windows
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        # Make the directories as needed
        for school_name in response.keys():
            os.makedirs(f"{tournament_id}/{school_name}", exist_ok=True)
            if not event.get("read_only", False):
                if "full_response" in response[school_name]:
                    with open(f"{tournament_id}/{school_name}/results.txt", "w") as f:
                        f.write(response[school_name]["full_response"])
            if "gpt_prompt" in response[school_name]:
                with open(f"{tournament_id}/{school_name}/gpt_prompt.txt", "w") as f:
                    f.write(response[school_name]["gpt_prompt"])
    else:
        # Save the tournament results to S3
        s3_client = boto3.client("s3")
        bucket_name = os.environ["DATA_BUCKET_NAME"]
        for school_name in response.keys():
            if "full_response" not in response[school_name]:
                logging.warning(f"No GPT response found for {school_name}")
                continue
            s3_client.put_object(
                Body=response[school_name]["full_response"],
                Bucket=bucket_name,
                Key=f"{tournament_id}/{school_name}/results.txt",
            )
            if "gpt_prompt" in response[school_name]:
                s3_client.put_object(
                    Body=response[school_name]["gpt_prompt"],
                    Bucket=bucket_name,
                    Key=f"{tournament_id}/{school_name}/gpt_prompt.txt",
                )


if __name__ == "__main__":
    event = {
        "tournament": "30799",  # "29810",  # "20134",
        "debug": True,
        "open_ai_key_path": "./openAiAuthKey.txt",  # Lives in root of the project
        "read_only": True,
    }
    handler(event, {})
