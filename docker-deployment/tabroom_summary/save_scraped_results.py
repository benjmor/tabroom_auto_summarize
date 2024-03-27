import boto3
import json
import os


def save_scraped_results(scrape_output, tournament_id):
    """
    This function saves the scraped results to a file so that we don't have to scrape tabroom every time we want to get
    the results of a tournament.
    """
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        # Save the scraped results to a file locally
        with open(f"{tournament_id}/scraped_results.json", "w") as f:
            f.write(json.dumps(scrape_output, indent=4))
        print(f"Scraped results saved to {tournament_id}/scraped_results.json")
    else:
        # Save the scraped results to S3
        s3_client = boto3.client("s3")
        bucket_name = os.environ["DATA_BUCKET_NAME"]
        s3_client.put_object(
            Body=json.dumps(scrape_output, indent=4),
            Bucket=bucket_name,
            Key=f"{tournament_id}/scraped_results.json",
        )
        print(
            f"Scraped results saved to s3://{bucket_name}/{tournament_id}/scraped_results.json"
        )
