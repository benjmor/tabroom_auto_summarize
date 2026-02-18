import boto3
import json
import logging
import os
import ssl
import urllib.request


def find_or_download_api_response(tournament_id, file_size_limit_mb: int = 5):
    # Check if the API response is already cached in S3. If it is, use that instead of re-scraping
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        file_location = f"{tournament_id}/api_response.json"
        if os.path.exists(file_location):
            with open(file_location, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logging.warning(
                        f"Failed to load {file_location}. Will attempt to download from tabroom.com"
                    )
    else:
        s3_client = boto3.client("s3")
        try:
            api_response_response = s3_client.get_object(
                Bucket=os.environ["DATA_BUCKET_NAME"],
                Key=f"{tournament_id}/api_response.json",
            )
            response_contents = json.loads(api_response_response["Body"].read())
            # If the size is larger than the 5MB threshold, raise an exception
            if (
                api_response_response["ContentLength"]
                > file_size_limit_mb * 1024 * 1024
            ):
                logging.warning(
                    f"BIG TOURNAMENT ALERT - Response size was {api_response_response["ContentLength"]}"
                )
            return response_contents

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
    # If the response is longer than the 5MB threshold, print a warning
    if len(json.dumps(response)) > file_size_limit_mb * 1024 * 1024:
        logging.warning(
            f"BIG TOURNAMENT ALERT - Response size was {len(json.dumps(response))}"
        )

    return response
