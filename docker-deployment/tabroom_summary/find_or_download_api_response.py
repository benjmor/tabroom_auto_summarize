import boto3
import json
import logging
import os
import ssl
import urllib.request


def find_or_download_api_response(tournament_id):
    # Check if the API response is already cached in S3. If it is, use that instead of re-scraping
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        file_location = f"{tournament_id}/api_response.json"
        if os.path.exists(file_location):
            with open(file_location, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logging.warning(
                        f"Failed to load {file_location}. Will attempt to download from tabroom.com"
                    )
    else:
        s3_client = boto3.client("s3")
        try:
            return json.loads(
                s3_client.get_object(
                    Bucket=os.environ["DATA_BUCKET_NAME"],
                    Key=f"{tournament_id}/api_response.json",
                )["Body"].read()
            )

        except s3_client.exceptions.NoSuchKey:
            logging.info(
                "No API response found in S3. Will attempt to download from tabroom.com"
            )
    # If we're still in this function, caching failed. Download the data from the Tabroom API
    # DOWNLOAD DATA FROM THE TABROOM API - We'll use a combination of this and scraping
    response = json.loads(
        urllib.request.urlopen(  # nosec - uses http
            url=f"http://www.tabroom.com/api/download_data.mhtml?tourn_id={tournament_id}",
            context=ssl._create_unverified_context(),  # nosec - data is all public
        ).read()
    )
    if "error" in response:
        raise ValueError(
            f"Error downloading data from Tabroom -- please check your tournament ID: {tournament_id}"
        )
    # Store the response for next time
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        os.makedirs(tournament_id, exist_ok=True)
        with open(file_location, "w") as f:
            f.write(json.dumps(response))
    else:
        s3_client.put_object(
            Body=json.dumps(response),
            Bucket=os.environ["DATA_BUCKET_NAME"],
            Key=f"{tournament_id}/api_response.json",
        )
    return response
