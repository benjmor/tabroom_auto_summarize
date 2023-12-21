from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse, parse_qs
import logging
from time import sleep
from scraper.parse_final_places_results import parse_final_places_results
from scraper.parse_prelim_records_results import parse_prelim_records_results
from scraper.parse_speaker_awards_results import parse_speaker_awards_results


def parse_results(input_data):
    """
    Function created to process all events in parallel.

    Returns a dictionary of events, each containing information about the event and any relevant results.
    Return format:
    {
        "event_name": <event_name>,
        "code_to_name_dict": {
            <code>: <name>,
            ...
        },
        "name_to_school_dict": {
            <name>: <school>
        },
        "result_list": [
            {
                "result_set_type": <result_set_type>,
                "results": [
                    "entry_name": <entry_name>,
                    "school_name": <school_name>",
                    <other keys>: <other values>
                ]
            }
        ],
    }
    """
    # Unpack input tuple -- invoking functions via Thread Executors requires a single argument that gets unpacked
    (
        option,
        base_url,
        chrome_options,
        final_results_identifiers,
        final_round_results_identifiers,
        scrape_entry_records,
    ) = input_data
    csv_map = {}
    code_to_name_dict_overall = {}
    name_to_school_dict_overall = {}
    name_to_full_name_dict_overall = {}
    result_contents = []
    try:
        event_name = option.get_attribute("innerHTML")
        csv_map[event_name] = {}
    except StaleElementReferenceException:
        logging.error("Error when attempting to load inner HTML.")
    try:
        value = option.get_attribute("value")
    except StaleElementReferenceException:
        logging.error("Error when attempting to load value.")
    link = f"{base_url}&event_id={value}"
    logging.info(f"Link to results for {event_name}: {link}")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 5)
    try:
        driver.get(link)
    except WebDriverException:
        sleep_time = 5
        logging.error(
            f"Error when attempting to load {link}. Sleeping for {sleep_time} seconds before trying again."
        )
        sleep(sleep_time)
        driver.get(link)
    driver.find_elements(By.CSS_SELECTOR, "div.sidenote a")
    result_pages = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.sidenote a"))
    )
    # Navigating through results. Make sure NOT to use the driver within the loop or you will break the loop's input!
    result_page_details = []
    for result in result_pages:
        result_name = result.text
        identifiers_dict = {
            "result_id": final_results_identifiers,
            "round_id": final_round_results_identifiers,
        }
        for id in identifiers_dict.keys():
            if result_name in identifiers_dict[id]:
                result_url = result.get_attribute("href")
                try:
                    result_id = parse_qs(urlparse(result_url).query)[id][0]
                except KeyError:
                    result_id = parse_qs(urlparse(result_url).query)["event_id"][0]
                result_page_details.append(
                    {
                        "result_id": result_id,
                        "result_url": result_url,
                        "result_name": result_name,
                    }
                )
    for result_page_detail in result_page_details:
        # Initialize these since not all paths will create it
        code_to_name_dict = {}
        name_to_school_dict = {}
        name_to_full_name_dict = {}
        driver.get(result_page_detail["result_url"])
        if result_page_detail["result_name"] == "Final Places":
            (
                result_table_content,
                code_to_name_dict,
                name_to_school_dict,
            ) = parse_final_places_results(
                driver,
                result_page_detail["result_id"],
            )
        elif result_page_detail["result_name"] == "Prelim Records":
            (
                result_table_content,
                code_to_name_dict,
                name_to_school_dict,
                name_to_full_name_dict,
            ) = parse_prelim_records_results(
                driver,
                scrape_entry_records,
            )
        elif result_page_detail["result_name"] == "Speaker Awards":
            result_table_content = parse_speaker_awards_results(driver)
        # TODO - Add support for more page types
        else:
            continue
        result_contents.append(result_table_content)
        code_to_name_dict_overall.update(code_to_name_dict)
        name_to_school_dict_overall.update(name_to_school_dict)
        name_to_full_name_dict_overall.update(name_to_full_name_dict)
    driver.quit()
    return {
        "event_name": event_name,
        "code_to_name_dict": code_to_name_dict_overall,
        "name_to_school_dict": name_to_school_dict_overall,
        "name_to_full_name_dict": name_to_full_name_dict_overall,
        "result_list": result_contents,
    }
