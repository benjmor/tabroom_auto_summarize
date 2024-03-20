import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import logging
from concurrent import futures
from .get_schools_and_states import get_schools_and_states
from .parse_results_wrapper import parse_results_wrapper
from .get_judge_map import get_judge_map
from .resolve_longname_to_shortname import resolve_longname_to_shortname
from collections import Counter
import boto3

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)

"""
Returns a dictionary with the following keys:
{
        "results" - A JSON with results data, including 
        "name_to_school_dict": name_to_school_dict_overall,
        "code_to_name_dict": code_to_name_dict_overall,
        "name_to_full_name_dict": name_to_full_name_dict_overall,
        "entry_counter_by_school": entry_counter_by_school,
        "school_set": school_set,
        "state_set": state_set,
    }
"""


def main(
    tournament_id,
    scrape_entry_records,
    chrome_options,
    chrome_service,
    data_bucket,
    final_results_identifiers=[
        "Final Places",
        "Prelim Seeds",  # Sometimes need to parse the prelim seeds to scrape name/entry data
        "Prelim Records",  # Often Used in tournaments that don't have elim rounds
        "Speaker Awards",  # API data doesn't differentiate individual speaker awards well
    ],
    final_round_results_identifiers=["Finals Round results"],
):
    code_to_name_dict_overall = {}
    name_to_school_dict_overall = {}
    name_to_full_name_dict_overall = {}
    # This browser will be the ONLY browser if running in single-process mode
    browser = webdriver.Chrome(options=chrome_options, service=chrome_service)
    logging.debug("Starting browser session")

    # Navigate to the page with the dropdown menu
    base_url = f"https://www.tabroom.com/index/tourn/results/index.mhtml?tourn_id={tournament_id}"
    browser.get(base_url)

    # Find the dropdown menu element and get its options
    dropdown = browser.find_element(By.NAME, "event_id")
    # select = Select(WebDriverWait(browser, 2).until(EC.visibility_of_any_elements_located((By.NAME, "event_id"))))
    event_options = dropdown.find_elements(By.TAG_NAME, "option")

    results = []
    # NOTE - Lambda runs in single-process mode
    if "--single-process" in chrome_options.arguments:
        # Grab the options data so that we don't have to loop over the dropdown again, which would require multiple browser windows
        event_options_tuples = []
        for event_option in event_options:
            event_options_tuples.append(
                (
                    event_option.get_attribute("innerHTML"),
                    event_option.get_attribute("value"),
                    event_option.text,
                )
            )
        for event_option in event_options_tuples:
            # If there is data in the temp_results folder in S3, load it into results
            s3_client = boto3.client("s3")
            try:
                response = s3_client.get_object(
                    Bucket=data_bucket,
                    Key=f"{tournament_id}/temp_results/{event_option[2]}.json",
                )
                results.append(json.loads(response["Body"].read()))
            except s3_client.exceptions.NoSuchKey:
                # If we're running in single-process mode, we don't want to open multiple browser windows
                # So we'll just run the parse_results function in the main thread
                single_event_result_data = parse_results_wrapper(
                    event_option=event_option,
                    base_url=base_url,
                    browser=browser,
                    final_results_identifiers=final_results_identifiers,
                    final_round_results_identifiers=final_round_results_identifiers,
                    scrape_entry_records=scrape_entry_records,
                )
                results.append(single_event_result_data)
                # At the end, save the event option into the temp_results folder
                s3_client.put_object(
                    Body=json.dumps(single_event_result_data),
                    Bucket=data_bucket,
                    Key=f"{tournament_id}/temp_results/{event_option[2]}.json",
                    ContentType="application/json",
                )
    else:
        thread_arguments = []
        # Pass options so that parallel processes can create their own browser sessions
        chrome_options_tuple = (
            chrome_options,
            chrome_service,
        )
        for event_option in event_options:
            # Add the value and text to the thread arguments
            thread_arguments.append(
                (
                    event_option,
                    base_url,
                    chrome_options_tuple,
                    final_results_identifiers,
                    final_round_results_identifiers,
                    scrape_entry_records,
                )
            )
        with futures.ThreadPoolExecutor(max_workers=len(thread_arguments)) as executor:
            results = list(
                executor.map(parse_results_wrapper, thread_arguments, timeout=600)
            )

    # Get attendee data
    school_set, state_set = get_schools_and_states(
        tournament_id=tournament_id,
        browser=browser,
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

    school_short_name_dict = {
        school: resolve_longname_to_shortname(school) for school in school_set
    }
    # Get a map of judges to schools
    judge_map = get_judge_map(
        tournament_id=tournament_id,
        browser=browser,
        school_short_name_dict=school_short_name_dict,
    )
    # Close the browser session
    browser.quit()
    return {
        "results": results,
        "name_to_school_dict": name_to_school_dict_overall,
        "code_to_name_dict": code_to_name_dict_overall,
        "name_to_full_name_dict": name_to_full_name_dict_overall,
        "entry_counter_by_school": dict(entry_counter_by_school),
        "school_set": list(school_set),
        "state_set": list(state_set),
        "judge_map": judge_map,
        "school_short_name_dict": school_short_name_dict,
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
