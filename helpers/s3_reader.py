import boto3
import json
import logging
import re
import texttable

# Set log level to info
logging.basicConfig(level=logging.INFO)

BUCKET_NAME = "tabroom-summaries-data-bucket"
s3_client = boto3.client("s3")
tournaments = []
tournaments_with_results = []
paginator = s3_client.get_paginator("list_objects")
result = paginator.paginate(Bucket=BUCKET_NAME, Delimiter="/")
for prefix in result.search("CommonPrefixes"):
    tournaments.append(prefix.get("Prefix"))

for tournament in tournaments:
    response = s3_client.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=tournament,
    )["Contents"]
    has_api_response = False
    has_results = False
    data_string = tournament
    for file in response:
        # Skip tournaments that don't have an API response field
        if re.search(r"api_response.json", file["Key"]):
            has_api_response = True
            tournament_data = json.loads(
                s3_client.get_object(
                    Bucket=BUCKET_NAME,
                    Key=tournament + "api_response.json",
                )["Body"]
                .read()
                .decode("utf-8")
            )
            data_object = {
                "tournament_id": tournament.replace("/", ""),
                "tournament_name": tournament_data["name"],
                "tournament_state": tournament_data["state"],
                "tournament_date": str(tournament_data["start"]),
            }
        if re.search(r"gpt_prompt.txt", file["Key"]):
            has_results = True
        if has_api_response and has_results:
            break
    if has_results and has_api_response:
        # Add new one to front of list
        tournaments_with_results.insert(0, list(data_object.values()))
    else:
        logging.warning(f"No results for {data_string}")

table = texttable.Texttable()
table.set_cols_align(["l", "l", "c", "c"])
table.set_cols_valign(["t", "t", "t", "t"])
table.set_max_width(0)
table.add_rows(
    [["Tournament ID", "Tournament Name", "State", "Date"]] + tournaments_with_results,
)
print(table.draw())
