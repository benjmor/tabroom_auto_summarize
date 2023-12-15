from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from scraper.scrape_entry_record import scrape_entry_record
import json


def parse_prelim_records_results(driver, scrape_entry_record_data: bool):
    """
    Walk through the results table.
    Returns 4 items in a tuple:
    1. Return a dict with a list of results by code, formatted like this:
    {
        "result_set_type": <result_set_type>,
        "results": [
        {
            name: <entry name>
            code: <entry code>
            school: <entry school>
            wins: <win count>
            # If we're scraping data
            scrape_entry_record_data: {
                full_entry_name: <full_entry_name>
                round_by_round_results: [
                    {
                        round_name: <round name>
                        side: <aff / neg >
                        opponent_code: <opp code>
                        win_ballots: <#>
                        loss_ballots:  <#>
                    },
                    ...
                    {...}
                ]
            }
        },
        ...
        {...}
    ]
    2. A dict that maps codes to entry names
    3. A dict that maps entry names to school names
    4. A dict that maps entry short names to full names (eg. Smith and Jones -> Joseph Smith and Bob Jones). Will be blank if not scraping entry records.
    """
    results_list = []
    code_to_name_dict = {}
    name_to_school_dict = {}
    name_to_full_name_dict = {}

    table = driver.find_element(By.ID, f"ranked_list")

    # Find the table headers
    headers = table.find_elements(By.CSS_SELECTOR, "thead th")
    if not headers:
        headers = table.find_elements(By.XPATH, "//th")

    header_names = [header.text for header in headers]
    # Get indices for headers
    # This is a fancy way of mapping non-standard header options to standardized values (eg. Name, Code)
    # Ultimately, we're just trying to get the column where each of these standard values lives
    index_dict = {
        "name": {"identifiers": ["Name", "Entry"], "index": -1},
        "code": {"identifiers": ["Code"], "index": -1},
        "school": {"identifiers": ["Institution", "School"], "index": -1},
        "wins": {"identifiers": ["Wins"], "index": -1},
    }
    for index, header_name in enumerate(header_names, start=0):
        for header_expected_name_key in index_dict.keys():
            if header_name in index_dict[header_expected_name_key]["identifiers"]:
                index_dict[header_expected_name_key]["index"] = index

    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    for row in rows:
        # Skip header rows (rows that use this funky yellowrow class name)
        # But also grab the column indices so we can check the school
        if row.get_attribute("class") == "yellowrow rotation odd":
            continue
        visible_results = [
            cell.text for cell in row.find_elements(By.CSS_SELECTOR, "td")
        ]
        entry_result = {}
        for header_expected_name_key in index_dict.keys():
            if index_dict[header_expected_name_key]["index"] != -1:
                entry_result[header_expected_name_key] = visible_results[
                    index_dict[header_expected_name_key]["index"]
                ]
                if header_expected_name_key == "name":
                    name_index = index_dict[header_expected_name_key]["index"]
                    entry_result["entry_record_url"] = (
                        row.find_elements(By.CSS_SELECTOR, "td")[name_index]
                        .find_element(By.CSS_SELECTOR, "a")
                        .get_attribute("href")
                    )
        results_list.append(entry_result)
        code_to_name_dict[entry_result["code"]] = entry_result["name"]
        name_to_school_dict[entry_result["name"]] = entry_result["school"]

    if scrape_entry_record_data:
        # TODO - Verify whether this updates in place
        for entry_result_dict in results_list:
            entry_result_dict["scrape_entry_record_data"] = scrape_entry_record(
                driver, entry_result_dict["entry_record_url"]
            )
            name_to_full_name_dict[entry_result_dict["name"]] = entry_result_dict[
                "scrape_entry_record_data"
            ]["full_entry_name"]
    results_dict = {"result_set_type": "Prelim Records", "results": results_list}
    return (
        results_dict,
        code_to_name_dict,
        name_to_school_dict,
        name_to_full_name_dict,
    )


if __name__ == "__main__":
    """
    This is for testing purposes
    """
    test_url = "https://www.tabroom.com/index/tourn/results/ranked_list.mhtml?event_id=258034&tourn_id=28356"
    # Start a new browser session
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # attempting to suppress the USB read errors on Windows
    # chrome_options.add_argument("--disable-logging")
    # chrome_options.binary_location = CHROME_PATH
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(test_url)
    print(
        json.dumps(
            parse_prelim_records_results(driver=browser, scrape_entry_record_data=True),
            indent=4,
        )
    )
