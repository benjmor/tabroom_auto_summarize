from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse, parse_qs
import logging
from time import sleep
from .parse_final_places_results import parse_final_places_results
from .parse_prelim_records_results import parse_prelim_records_results
from .parse_speaker_awards_results import parse_speaker_awards_results
from .parse_district_qualifiers import parse_district_qualifiers
from .parse_dicts_from_prelim_seeds import parse_dicts_from_prelim_seeds
from .parse_dicts_from_prelim_chambers import parse_dicts_from_prelim_chambers
import os
import re 


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
    IS_NSDA_NATIONALS = os.getenv("IS_NSDA_NATIONALS", "false") == "true"

    # Unpack input tuple -- invoking functions via Thread Executors requires a single argument that gets unpacked
    (
        option,
        base_url,
        browser,
        final_results_identifiers,
        final_round_results_identifiers,
        scrape_entry_records,
    ) = input_data
    code_to_name_dict_overall = {}
    name_to_school_dict_overall = {}
    name_to_full_name_dict_overall = {}
    result_contents = []
    if isinstance(option, tuple):
        # unpack the tuple
        event_name, value = option
    else:
        try:
            event_name = option.get_attribute("innerHTML")
            value = option.get_attribute("value")
        except StaleElementReferenceException:
            logging.error("Error when attempting to load option value.")
    link = f"{base_url}&event_id={value}"
    logging.info(f"Link to results for {event_name}: {link}")
    wait = WebDriverWait(browser, 3)
    try:
        logging.info(f"Attempting to load {link}")
        browser.get(url=link)
        logging.info(f"Loaded {link}")
    except WebDriverException:
        sleep_time = 3
        logging.error(
            f"Error when attempting to load {link}. Sleeping for {sleep_time} seconds before trying again."
        )
        sleep(sleep_time)
        browser.get(link)
    browser.find_elements(By.CSS_SELECTOR, "div.sidenote a")
    try:
        result_pages = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.sidenote a"))
        )
    except TimeoutException:
        logging.error(f"Could not find event {event_name} in page elements")
        return {
            "event_name": event_name,
            "code_to_name_dict": {},
            "name_to_school_dict": {},
            "name_to_full_name_dict": {},
            "result_list": [],
        }
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
        browser.get(result_page_detail["result_url"])
        if re.search(r"Prelim Chamber Results", result_page_detail["result_name"]):
            # This is a special case for NSDA Congress results
            # We don't parse these results here, but we do need to extract the names and schools
            result_table_content = {}
            code_to_name_dict, name_to_school_dict, name_to_full_name_dict = (
                parse_dicts_from_prelim_chambers(
                    driver=browser,
                    result_url=result_page_detail["result_url"],
                )
            )
        elif result_page_detail["result_name"] == "Final Places":
            (
                result_table_content,
                code_to_name_dict,
                name_to_school_dict,
            ) = parse_final_places_results(
                browser,
                result_page_detail["result_id"],
            )
        elif (
            result_page_detail["result_name"] == "Prelim Records"
            and not IS_NSDA_NATIONALS  # NSDA Nationals Prelim Records are anonymized
        ):
            (
                result_table_content,
                code_to_name_dict,
                name_to_school_dict,
                name_to_full_name_dict,
            ) = parse_prelim_records_results(
                scrape_entry_record_data=scrape_entry_records,
                browser=browser,
                result_url=result_page_detail["result_url"],
            )
        elif result_page_detail["result_name"] == "Prelim Seeds":
            (
                code_to_name_dict,
                name_to_school_dict,
            ) = parse_dicts_from_prelim_seeds(
                driver=browser,
                result_url=result_page_detail["result_url"],
            )
            result_table_content = {}
        elif result_page_detail["result_name"] == "Speaker Awards":
            result_table_content = parse_speaker_awards_results(browser)

        elif result_page_detail["result_name"] == "District Qualifiers":
            (
                result_table_content,
                name_to_school_dict,
            ) = parse_district_qualifiers(browser)
        # TODO - Add support for more page types
        else:
            continue
        result_contents.append(result_table_content)
        code_to_name_dict_overall.update(code_to_name_dict)
        name_to_school_dict_overall.update(name_to_school_dict)
        name_to_full_name_dict_overall.update(name_to_full_name_dict)
    logging.info(f"Finished parsing {event_name}!")
    return {
        "event_name": event_name,
        "code_to_name_dict": code_to_name_dict_overall,
        "name_to_school_dict": name_to_school_dict_overall,
        "name_to_full_name_dict": name_to_full_name_dict_overall,
        "result_list": result_contents,
    }
