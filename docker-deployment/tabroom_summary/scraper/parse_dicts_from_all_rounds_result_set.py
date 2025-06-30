from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import logging
import selenium

def parse_dicts_from_all_rounds_result_set(
    driver,
    result_url,
):
    # Walk through the prelim chambers table and map student name to school name

    name_to_school_dict = {}

    # Get the table element by ID
    result_id = result_url.split("=")[-1]
    all_rounds_table = driver.find_element(By.CSS_SELECTOR, "table.tablesorter")
    if not all_rounds_table:
        logging.warning(f"No tables found for result ID {result_id}")
    all_rows = all_rounds_table.find_elements(By.CSS_SELECTOR, "tbody tr")
    for each_row in all_rows:
        row_values = each_row.find_elements(By.CLASS_NAME, "smallish")
        name_to_school_dict[row_values[0].text] = row_values[1].text
    return name_to_school_dict