"""
Summary
This Lambda will look at the upcoming tournaments in the next week and save them to a DynamoDB

The Lambda will then kick off a process (step function?) to look for results for existing tournaments

The output will eventually be GPT prompts for every tournament that completed since the last run.

This will NOT be backwards-looking -- it will only run on tournaments that start after 2024-03-17.
"""

import datetime
import os
from selenium import webdriver
from tempfile import mkdtemp
from selenium.webdriver.common.by import By


options = webdriver.ChromeOptions()
# If we're not in Lambda, assume we're in Windows
if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
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
    )
    # TODO - add logic for January tournaments that show up in November/December
    current_year = datetime.now().year
    print(f"Tournament ID: {tournament_id} ends {end_date}")
    # TODO - Store the tournament ID and end date in DynamoDB
    data_to_store = {
        "tournament_id": tournament_id,
        "end_date": end_date,
        "prompts_generated": False,
    }
browser.quit()
