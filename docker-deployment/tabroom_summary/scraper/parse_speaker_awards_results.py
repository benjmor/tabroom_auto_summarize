from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import selenium
import logging


def parse_speaker_awards_results(driver):
    """
    Given a Selenium driver with the URL of a speaker awards page, parse the speaker awards table

    Returns a dict with the result set type and speaker results
    {
        "result_set_type": <result_set_type>,
        "results": [
            {
                place: <placement>
                name: <entry full name>
                code: <entry code>
                school: <entry school>
                wins: <win count>
                tiebreaker_data: {
                    <key-value pairs for tiebreaker columns>
                }
            },
            ...
            {...}
        ]
    }
    """
    results_list = []
    try:
        table = driver.find_element(By.CLASS_NAME, f"tablesorter")
    except selenium.common.exceptions.NoSuchElementException:
        logging.debug("No table found, this may indicate results not published.")
        return results_list
    # Find the table headers
    headers = table.find_elements(By.CSS_SELECTOR, "thead th")
    if not headers:
        headers = table.find_elements(By.XPATH, "//th")

    header_names = [header.text for header in headers]
    # Get indices for headers
    # This is a fancy way of mapping non-standard header options to standardized values (eg. Name, Code)
    # Ultimately, we're just trying to get the column where each of these standard values lives
    index_dict = {
        "place": {"identifiers": ["Place"], "index": -1},
        "first_name": {"identifiers": ["First"], "index": -1},
        "last_name": {"identifiers": ["Last"], "index": -1},
        "code": {"identifiers": ["Entry", "Code"], "index": -1},
        "school": {"identifiers": ["Institution", "School"], "index": -1},
        "state": {"identifiers": ["State"], "index": -1},
    }
    header_map = {}  # Maps official tabroom headers to snake_case headers
    for index, header_name in enumerate(header_names, start=0):
        for header_expected_name_key in index_dict.keys():
            if header_name in index_dict[header_expected_name_key]["identifiers"]:
                index_dict[header_expected_name_key]["index"] = index
                header_map[header_name] = header_expected_name_key

    rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
    for row in rows:
        # Skip header rows (rows that use this funky yellowrow class name)
        # But also grab the column indices so we can check the school
        if row.get_attribute("class") == "yellowrow rotation odd":
            continue
        visible_results = [
            cell.text for cell in row.find_elements(By.CSS_SELECTOR, "td")
        ]
        entry_result = {"tiebreaker_data": {}}
        for iterator, header_expected_name_key in enumerate(header_names):
            if header_expected_name_key == "":
                continue
            try:
                entry_result[header_map[header_expected_name_key]] = visible_results[
                    index_dict[header_map[header_expected_name_key]]["index"]
                ]
            except KeyError:
                entry_result["tiebreaker_data"][header_expected_name_key] = (
                    visible_results[iterator]
                )
        # Get the hidden data which contains speaker points by round
        try:
            entry_result["round_by_round"] = (
                (row.find_element(By.XPATH, './/td[@class="hiddencsv"]'))
                .get_attribute("innerHTML")
                .strip()
            )
        except Exception:
            pass

        # Move tiebreaker data to end of dict to make it easier to read lol
        tiebreaker_temp = entry_result["tiebreaker_data"]
        del entry_result["tiebreaker_data"]
        entry_result["tiebreaker_data"] = tiebreaker_temp

        # Merge first and last name
        full_name = entry_result["first_name"] + " " + entry_result["last_name"]
        entry_result["name"] = full_name
        del entry_result["first_name"]
        del entry_result["last_name"]

        # Add the results to the output
        results_list.append(entry_result)

    return {
        "result_set_type": "Speaker Awards",
        "results": results_list,
    }


if __name__ == "__main__":
    """
    This is for testing purposes
    """
    test_url = "https://www.tabroom.com/index/tourn/results/event_results.mhtml?tourn_id=29228&result_id=287536"
    # Start a new browser session
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # attempting to suppress the USB read errors on Windows
    # chrome_options.add_argument("--disable-logging")
    # chrome_options.binary_location = CHROME_PATH
    service = webdriver.ChromeService(executable_path="/opt/chromedriver")
    browser = webdriver.Chrome(options=chrome_options, service=service)
    browser.get(test_url)
    print(
        json.dumps(
            parse_speaker_awards_results(driver=browser),
            indent=4,
        )
    )
    browser.quit()
