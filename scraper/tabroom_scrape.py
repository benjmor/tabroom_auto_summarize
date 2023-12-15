import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import logging
from concurrent import futures
from scraper.get_schools_and_states import get_schools_and_states
from scraper.parse_results import parse_results
from collections import Counter

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)


def main(
    tournament_id,
    scrape_entry_records,
    final_results_identifiers=[
        "Final Places",
        "Prelim Seeds",  # Sometimes need to parse the prelim seeds to scrape name/entry data
        "Prelim Records",  # Often Used in tournaments that don't have elim rounds
    ],  # ["Speaker Awards", "Final Places"]
    final_round_results_identifiers=["Finals Round results"],
):
    code_to_name_dict_overall = {}
    name_to_school_dict_overall = {}
    name_to_full_name_dict_overall = {}
    # Start a new browser session
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # attempting to suppress the USB read errors on Windows
    # chrome_options.add_argument("--disable-logging")
    # chrome_options.binary_location = CHROME_PATH
    browser = webdriver.Chrome(options=chrome_options)

    # Navigate to the page with the dropdown menu
    base_url = f"https://www.tabroom.com/index/tourn/results/index.mhtml?tourn_id={tournament_id}"
    browser.get(base_url)

    # Find the dropdown menu element and get its options
    dropdown = browser.find_element(By.NAME, "event_id")
    # select = Select(WebDriverWait(browser, 2).until(EC.visibility_of_any_elements_located((By.NAME, "event_id"))))
    options = dropdown.find_elements(By.TAG_NAME, "option")

    thread_arguments = []
    for option in options:
        # Add the value and text to the thread arguments
        thread_arguments.append(
            (
                option,
                base_url,
                chrome_options,
                final_results_identifiers,
                final_round_results_identifiers,
                scrape_entry_records,
            )
        )

    # Loop through the options and scrape their child links
    with futures.ThreadPoolExecutor(10) as executor:
        results = list(executor.map(parse_results, thread_arguments))

    # Get attendee data
    school_set, state_set = get_schools_and_states(
        tournament_id=tournament_id,
        chrome_options=chrome_options,
    )

    # Get a counter with how many entries were from each school, for funsies
    entry_schools = []
    for result in results:
        for each_item in result["name_to_school_dict"].keys():
            entry_schools.append(result["name_to_school_dict"][each_item])
        name_to_school_dict_overall.update(result["name_to_school_dict"])
        code_to_name_dict_overall.update(result["code_to_name_dict"])
        name_to_full_name_dict_overall.update(result["name_to_full_name_dict"])
    entry_counter_by_school = Counter(entry_schools)

    # State set can be zero (assume it's intrastate), but scrape schools if 'Institutions in Attendance' is not published
    if len(school_set) == 0:
        logging.warning("No schools found -- aggregating data from results")
        school_set = set(entry_schools)

    # Close the browser session
    browser.quit()
    return {
        "results": results,
        "name_to_school_dict": name_to_school_dict_overall,
        "code_to_name_dict": code_to_name_dict_overall,
        "name_to_full_name_dict": name_to_full_name_dict_overall,
        "entry_counter_by_school": entry_counter_by_school,
        "school_set": school_set,
        "state_set": state_set,
    }


if __name__ == "__main__":
    # This is not intended to be called as a main routine but is here for testing purposes.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--tournament-id",
        help="Tournament ID (typically a 5-digit number) of the tournament you want to generate results for.",
        # required=True,
        default="28356",
    )
    parser.add_argument(
        "-s",
        "--scrape-entry-records",
        help="If set, this flag will scrape entry records from debate events that have 'Prelim Records' pages. This will cause the scraper to take longer, but generates richer data.",
        action="store_true",
        default=True,
    )
    args = parser.parse_args()
    tournament_id = args.tournament_id
    scrape_entry_records_bool = args.scrape_entry_records
    results = main(
        tournament_id=tournament_id,
        scrape_entry_records=scrape_entry_records_bool,
    )
    print(json.dumps(results), indent=2)
