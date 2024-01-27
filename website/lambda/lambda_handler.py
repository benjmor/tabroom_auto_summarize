import json
import boto3
import os


def lambda_handler(event, context):
    print(event)
    # Do some data validation -- ensure that the number is 5 digits and the school name is 50 characters or less
    s3_client = boto3.client("s3")
    parsed_body = json.loads(event["body"])
    tournament_id = parsed_body["tournament"]
    school_name = parsed_body["school"]
    file_path_to_find_or_create = f"{tournament_id}/{school_name}/results.txt"
    raw_gpt_submission = f"{tournament_id}/{school_name}/gpt_prompt.txt"
    bucket_name = os.environ["DATA_BUCKET_NAME"]
    file_exists = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=file_path_to_find_or_create
    )
    if "Contents" in file_exists:
        file_content = s3_client.get_object(
            Bucket=bucket_name, Key=file_path_to_find_or_create
        )
        gpt_content = s3_client.get_object(
            Bucket=bucket_name, Key=raw_gpt_submission
        )
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "file_content": file_content["Body"].read().decode("utf-8"),
                    "gpt_content": gpt_content["Body"].read().decode("utf-8"),
                }
            ),
        }
    else:
        # Check if there are any files in the path bucket_name/tournament_id
        all_objects=s3_client.list_objects_v2(
            Bucket=bucket_name, Prefix=tournament_id,
        )
        if all_objects["KeyCount"] > 0:
            return {
                "statusCode": 200,
                "body": json.dumps("Tournament exists, but school does not. Check that your school name matches the official name."),
            }
        return {
            "statusCode": 200,
            "body": json.dumps("File does not exist, consider generating it"),
        }
