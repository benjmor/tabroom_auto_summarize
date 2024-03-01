import json
import boto3
import os
from datetime import datetime, timedelta


def lambda_handler(event, context):
    print(event)
    cors_headers = {
        "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
    }

    # Do some data validation -- ensure that the number is 5 digits and the school name is 50 characters or less
    s3_client = boto3.client("s3")
    parsed_body = json.loads(event["body"])
    parsed_body["read_only"] = os.environ["READ_ONLY"]
    tournament_id = parsed_body["tournament"]
    school_name = str(parsed_body["school"]).strip()
    file_path_to_find_or_create = f"{tournament_id}/{school_name}/results.txt"
    raw_gpt_submission = f"{tournament_id}/{school_name}/gpt_prompt.txt"
    api_response_key = f"{tournament_id}/api_response.json"
    bucket_name = os.environ["DATA_BUCKET_NAME"]

    # Check if the requested results already exist -- return them if they do
    gpt_file_exists = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=raw_gpt_submission,
    )
    if "Contents" in gpt_file_exists:
        try:
            file_content = (
                s3_client.get_object(
                    Bucket=bucket_name,
                    Key=file_path_to_find_or_create,
                )["Body"]
                .read()
                .decode("utf-8")
            )
        except Exception:
            file_content = "Prompt was not passed to ChatGPT; you can send the below prompt manually."
        gpt_content = (
            s3_client.get_object(
                Bucket=bucket_name,
                Key=raw_gpt_submission,
            )["Body"]
            .read()
            .decode("utf-8")
        )
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "file_content": file_content,
                    "gpt_content": gpt_content,
                }
            ),
        }
    else:
        # If the API response file exists in S3 and is larger than 5MB, return an error message and exit
        try:
            api_response_content = s3_client.get_object_attributes(
                Bucket=bucket_name,
                Key=api_response_key,
                ObjectAttributes=["ObjectSize"],
            )
            api_response_size = api_response_content["ObjectSize"]
            if api_response_size > 5 * 1024 * 1024:
                return {
                    "isBase64Encoded": False,
                    "statusCode": 400,
                    "headers": cors_headers,
                    "body": json.dumps(
                        {
                            "error": "API response is too large. Please reach out to the Issues page at https://github.com/benjmor/tabroom_auto_summarize/issues to request results for large tournaments."
                        }
                    ),
                }
        except Exception:
            # If there is no api_response.json, chug along normally -- we'll download and quit if necessary.
            pass
        # Check if there are any files in the path bucket_name/tournament_id
        all_objects = s3_client.list_objects_v2(
            Bucket=bucket_name,
            Prefix=tournament_id,
        )
        # If there are no files at all, then skip this section and kick off a results generation
        if all_objects["KeyCount"] > 0:
            # See if a placeholder file exists -- used to prevent duplicate runs
            # placeholder.txt is a good proxy of whether a Lambda is currently running or failed ungracefully
            try:
                placeholder_attributes = s3_client.get_object_attributes(
                    Bucket=bucket_name,
                    Prefix=f"{tournament_id}/placeholder.txt",
                )
            except Exception:
                placeholder_attributes = None

            # Get a list of all the schools in the tournament so that the user knows what they can choose from
            school_set = set()
            for obj in all_objects["Contents"]:
                # Don't include files in the root of the tournament
                if len(obj["Key"].split("/")) > 2:
                    school_set.add(obj["Key"].split("/")[1])
            # Display the school list if there are schools present
            if len(school_set) > 0:
                school_data = "\n\n".join(sorted(list(school_set)))
            # Otherwise, display a message indicating the status
            else:
                # Placeholder is present but no school results ready -- have the user wait for results
                if (
                    placeholder_attributes is not None
                    and datetime(placeholder_attributes["LastModified"])
                    + timedelta(hours=1)
                    > datetime.now()
                ):
                    school_data = "Still generating results! Check back soon!\nConsider opening a GitHub issue at https://github.com/benjmor/tabroom_auto_summarize/issues if this message persists."
                # no school results are present AND (the placeholder file is missing or outdated) -- data should be regenerated.
                else:
                    school_data = "No schools found; will attempt to regenerate."
                    s3_client.put_object(
                        Body="Placeholder during generation.",
                        Bucket=bucket_name,
                        Key=f"{tournament_id}/placeholder.txt",
                    )
                    lambda_client = boto3.client("lambda")
                    lambda_client.invoke(
                        FunctionName=os.environ["TABROOM_SUMMARY_LAMBDA_NAME"],
                        InvocationType="Event",
                        Payload=json.dumps(parsed_body),
                    )
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(
                    {
                        "file_content": (
                            "Tournament exists, but school does not. "
                            + "Check that your school name matches the official name. "
                            + f"Schools with results:\n\n{school_data}"
                        ),
                        "gpt_content": "N/A",
                    }
                ),
            }
        # Put a placeholder file in the S3 bucket and then trigger the Lambda to generate the GPT prompts and results
        s3_client.put_object(
            Body="Placeholder during generation.",
            Bucket=bucket_name,
            Key=f"{tournament_id}/placeholder.txt",
        )
        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName=os.environ["TABROOM_SUMMARY_LAMBDA_NAME"],
            InvocationType="Event",
            Payload=json.dumps(parsed_body),
        )
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "file_content": "Results not yet generated, will attempt to generate them. Check back in about 15 minutes.\nNote: larger tournaments (eg. Harvard) are not supported through this web interface.\nCreate an Issue at https://github.com/benjmor/tabroom_auto_summarize/issues if you want results from a specific large tournament.",
                    "gpt_content": "N/A",
                }
            ),
        }
