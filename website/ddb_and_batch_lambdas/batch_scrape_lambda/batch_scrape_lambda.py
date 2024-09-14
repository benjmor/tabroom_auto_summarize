"""
Summary
This Lambda will look at the upcoming tournaments in the next week and save them to a DynamoDB

The Lambda will then kick off a process (step function?) to look for results for existing tournaments

The output will eventually be LLM prompts for every tournament that completed since the last run.

This will NOT be backwards-looking -- it will only run on tournaments that start after 2024-09-09.
"""

import datetime
import json
import logging
import os
import boto3
from selenium import webdriver
from tempfile import mkdtemp
from selenium.webdriver.common.by import By

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

def store_data_in_ddb(
    data: dict,
    ddb_name: str,
):
    if ddb_resource is None:
        ddb_resource = boto3.resource(
            "dynamodb",
            # region_name=REGION,
        )
    table = ddb_resource.Table(ddb_name)
    # Check if the item's tourn_id already exists in the table
    tourn_id = data["tourn_id"]
    response = table.get_item(Key={"tourn_id": tourn_id})
    if "Item" in response:
        logging.info(f"Item with tourn_id {tourn_id} already exists in the table.")
        {
            "statusCode": 200,
            "body": json.dumps(
                f"Item with tourn_id {tourn_id} already exists in the table."
            ),
        }
    try:
        # Insert the item into the table
        response = table.put_item(Item=data)
        logging.info("PutItem succeeded:", response)
        return {
            "statusCode": 200,
            "body": json.dumps("Item successfully inserted."),
        }
    except Exception as e:
        logging.info("Error inserting item:", e)
        return {
            "statusCode": 500,
            "body": json.dumps("Error inserting item."),
        }


def find_upcoming_tournaments(
    browser,
    ddb_table_name,
):
    new_tournament_count = 0

    browser.get("https://www.tabroom.com/index/index.mhtml")
    # Get all rows in the table

    # Get the Table
    browser.find_element(by=By.ID, value="tournlist")
    # Get the table body
    browser.find_element(by=By.CLASS_NAME, value="smaller")
    # Get all the rows
    all_rows = browser.find_elements(by=By.TAG_NAME, value="tr")
    for row in all_rows:
        cells = row.find_elements(by=By.TAG_NAME, value="td")
        if not cells:
            continue  # Skip empty rows
        raw_date = str(cells[0].text)
        try:
            end_date = raw_date.split("-")[1].strip()
        except IndexError:
            end_date = raw_date.strip()
        tournament_id = (
            cells[1]
            .find_element(By.CLASS_NAME, "white")
            .get_attribute("href")
            .split("/")[-1]
        ).split("=")[-1]
        tournament_name = cells[1].find_element(By.CLASS_NAME, "white").text
        locality = cells[3].find_element(By.CLASS_NAME, "white").text
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        end_date_month = end_date.split("/")[0]
        end_date_day = end_date.split("/")[1]
        # build a datetime value out of the end date and current year
        date_str = f"{end_date}/{current_year}"
        date_obj = datetime.datetime.strptime(date_str, "%m/%d/%Y")
        formatted_date_str = date_obj.strftime("%Y-%m-%d")

        if current_month > int(end_date_month):
            logging.warning(
                f"Skipping next-year tournament {tournament_id} ({tournament_name})"
            )
            continue

        data_to_store = {
            "tourn_id": tournament_id,
            "tourn_name": tournament_name,
            "end_date": formatted_date_str,
            "locality": locality,
            "prompts_generated": False,
        }
        logging.info(f"Tournament data: {data_to_store}")
        store_data_in_ddb(
            data=data_to_store,
            ddb_name=ddb_table_name,
        )
        new_tournament_count += 1
    boto3.client("sns").publish(
        Message=f"Completed tournament scrape. {new_tournament_count} tournaments were added.",
        TopicArn=os.environ.get("SNS_TOPIC_ARN"),
    )


def lambda_handler(event, context):
    env_var_ddb_table = os.environ.get("DDB_TABLE_NAME")
    options = webdriver.ChromeOptions()

    # If we're not in Lambda, assume we're in Windows
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        env_var_ddb_table = "tabroom_tournaments"
        chrome_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        driver_location = None  # Use default
        service = webdriver.ChromeService()
        options.binary_location = chrome_location
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # If we are in Lambda, assume we're in Linux
    else:
        chrome_location = "/opt/chrome/chrome"
        driver_location = "/opt/chromedriver"
        service = webdriver.ChromeService(driver_location)
        options.binary_location = chrome_location
        options.add_argument("--single-process")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9222")

    options.add_argument("--headless=new")

    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    browser = webdriver.Chrome(options=options)
    find_upcoming_tournaments(
        browser=browser,
        ddb_table_name=env_var_ddb_table,
    )
    browser.quit()


if __name__ == "__main__":
    lambda_handler({}, {})
