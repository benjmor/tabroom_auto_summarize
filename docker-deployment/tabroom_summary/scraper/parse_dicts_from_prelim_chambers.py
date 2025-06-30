from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import logging
import selenium


def parse_dicts_from_prelim_chambers(
    driver,
    result_url,
):
    """
    Walk through the prelim chambers table and gather school/code information into the dicts.
    1. A dict that maps codes to entry names
    2. A dict that maps entry names to school names
    3. A dict that maps entry names to full names
    """
    code_to_name_dict = {}
    name_to_school_dict = {}
    name_to_full_name_dict = {}

    # Get the table element by ID
    result_id = result_url.split("=")[-1]
    all_tables = driver.find_elements(By.CSS_SELECTOR, "table.tablesorter")
    if not all_tables:
        logging.warning(f"No tables found for result ID {result_id}")
    for each_table in all_tables:
        all_rows = each_table.find_elements(By.CSS_SELECTOR, "tbody tr")
        for each_row in all_rows:
            row_values = each_row.find_elements(By.CLASS_NAME, "smallish")
            name_to_school_dict[row_values[0].text] = row_values[1].text
    return code_to_name_dict, name_to_school_dict, name_to_full_name_dict
