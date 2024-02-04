from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    StaleElementReferenceException,
)
import json
import logging
import re
import selenium
from .parse_hidden_string import parse_hidden_string


def parse_final_places_results(driver, result_id):
    """
    Walk through the results table.
    Returns 3 items in a tuple:
    1. Return a dict with a list of results by code, formatted like this:
    {
        "result_set_type": "Final Places",
        "results": [
        {
            "entry_name": <entry name>,
            "school_name": <entry school>,
            <various other key-value pairs, such as Place, Tiebreakers, and round-by-round performance>
        },
        ...
        {...}
    ]
    2. A dict that maps codes to entry names
    3. A dict that maps entry names to school names
    """
    results_list = []
    code_to_name_dict = {}
    name_to_school_dict = {}
    table_num = 0
    # Walk through the results tables until we run out of tables
    done = False
    while not done:
        table_num = table_num + 1
        try:
            element_id = f"{result_id}-{table_num}"
            table = driver.find_element(By.ID, f"{result_id}-{table_num}")
        except selenium.common.exceptions.NoSuchElementException:
            logging.debug(
                f"No table found for element ID {element_id}, trying without table number"
            )
            try:
                done = True  # Without a table number, we assume 1 table and break at the end
                element_id = result_id
                table = driver.find_element(By.ID, f"{element_id}")
            except selenium.common.exceptions.NoSuchElementException:
                logging.debug(f"No table found for element ID {element_id}, either")
                break
        # Find the table headers
        headers = table.find_elements(By.CSS_SELECTOR, "thead th")
        if not headers:
            headers = table.find_elements(By.XPATH, "//th")

        header_names = [header.text for header in headers]
        index_dict = {
            "name": {"identifiers": ["Name", "Entry"], "index": -1},
            "code": {"identifiers": ["Code"], "index": -1},
            "school": {"identifiers": ["Institution", "School"], "index": -1},
        }
        for index, header_name in enumerate(header_names, start=0):
            for header_expected_name_key in index_dict.keys():
                if header_name in index_dict[header_expected_name_key]["identifiers"]:
                    index_dict[header_expected_name_key]["index"] = index

        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        for row in rows:
            result = {}
            # Skip header rows (rows that use this funky yellowrow class name)
            # But also grab the column indices so we can check the school
            if row.get_attribute("class") == "yellowrow rotation odd":
                continue
            visible_results = [
                cell.text for cell in row.find_elements(By.CSS_SELECTOR, "td")
            ]
            # Add that hidden CSV if it's there because we love it -- it contains round-by-round debate results
            try:
                hidden_csv_string = (
                    (row.find_element(By.XPATH, './/td[@class="hiddencsv"]'))
                    .get_attribute("innerHTML")
                    .strip()
                )

                result["round_by_round"] = parse_hidden_string(hidden_csv_string)

            except selenium.common.exceptions.NoSuchElementException:
                logging.debug(
                    f"Could not add hidden results table for element ID {element_id}. This is normal for speech events, but weird for debate."
                )
            for i in range(len(header_names)):
                # Skip empty headers
                if header_names[i] != "":
                    result[header_names[i]] = visible_results[i]
            results_list.append(result)
            # Skip if Code is not defined
            if index_dict["code"]["index"] != -1:
                code_to_name_dict[
                    visible_results[index_dict["code"]["index"]]
                ] = visible_results[index_dict["name"]["index"]]
            name_to_school_dict[
                visible_results[index_dict["name"]["index"]]
            ] = visible_results[index_dict["school"]["index"]]
    results_dict = {
        "result_set_type": "Final Places",
        "results": results_list,
    }
    return (
        results_dict,
        code_to_name_dict,
        name_to_school_dict,
    )


if __name__ == "__main__":
    """
    This is for testing purposes
    """
    test_url = "https://www.tabroom.com/index/tourn/results/event_results.mhtml?tourn_id=24104&result_id=245220"
    test_result_id = "245220"
    # Start a new browser session
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # attempting to suppress the USB read errors on Windows
    # chrome_options.add_argument("--disable-logging")
    # chrome_options.binary_location = CHROME_PATH
    service = webdriver.ChromeService(executable_path='/usr/bin/chromedriver')
    browser = webdriver.Chrome(options=chrome_options, service=service)
    browser.get(test_url)
    print(
        json.dumps(
            parse_final_places_results(
                driver=browser,
                result_id=test_result_id,
            ),
            indent=4,
        )
    )
