import json
import boto3
import os


def lambda_handler(event, context):
    print(event)
    # Do some data validation -- ensure that the number is 5 digits and the school name is 50 characters or less
    s3_client = boto3.client("s3")
    file_path_to_find_or_create = event["queryStringParameters"]["file_path"]
    bucket_name = os.environ["DATA_BUCKET_NAME"]
    file_exists = s3_client.list_objects_v2(
        Bucket=bucket_name, Prefix=file_path_to_find_or_create
    )
    if "Contents" in file_exists:
        return {"statusCode": 200, "body": json.dumps("File exists")}
    else:
        # TODO - At some point, test if the tournament results exist but the school is not present. That should be a failure returned to the user.
        return {
            "statusCode": 200,
            "body": json.dumps("File does not exist, consider generating it"),
        }
