import boto3
import json
import logging
import urllib.request
import os
import ssl
import datetime
from selenium import webdriver
from tempfile import mkdtemp
from .scraper import tabroom_scrape as tabroom_scrape
from .update_global_entry_dictionary import update_global_entry_dictionary
from .parse_arguments import parse_arguments
from .group_data_by_school import group_data_by_school
from .generate_chat_gpt_paragraphs import generate_chat_gpt_paragraphs
from .parse_result_sets import parse_result_sets
from .save_scraped_results import save_scraped_results
from .find_or_download_api_response import find_or_download_api_response


def main(
    school_name: str = "",
    tournament_id: str = "",
    all_schools: bool = False,
    custom_url: str = "",
    read_only: bool = False,
    percentile_minimum: int = 40,
    max_results_to_pass_to_gpt: int = 15,
    context: str = "",
    scrape_entry_records_bool: bool = True,
    open_ai_key_path: str = None,
    open_ai_key_secret_name: str = None,
    debug: bool = False,
):
    response_data = find_or_download_api_response(tournament_id)
    response_data["id"] = tournament_id
    # Fail early if tournament's end date is in the future or there are no results
    if (
        "end_date" in response_data
        and response_data["end_date"] > datetime.datetime.now().isoformat()
    ):
        logging.warning(
            f"Tournament end date is in the future: {response_data['end_date']}"
        )
        raise ValueError("Tournament has not ended yet")

    options = webdriver.ChromeOptions()
    # If we're not in Lambda, assume we're in Windows
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        chrome_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        driver_location = None  # Use default
    # If we are in Lambda, assume we're in Linux
    else:
        chrome_location = "/opt/chrome/chrome"
        driver_location = "/opt/chromedriver"

    if debug is True:
        service = webdriver.ChromeService()
        options.binary_location = chrome_location
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
    else:
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

    # SCRAPE TABROOM FOR ALL THE GOOD DATA NOT PRESENT IN THE API
    # Check if we need to scrape the entry records
    must_scrape = True
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
        file_location = f"{tournament_id}/scraped_results.json"
        if os.path.exists(file_location):
            try:
                with open(file_location, "r") as f:
                    scrape_output = json.load(f)
                must_scrape = False
            except json.JSONDecodeError:
                logging.info("Scraped results file is corrupted. Scraping tabroom.com")
                must_scrape = True
        else:
            logging.info(
                "No scraped results found in the local directory. Scraping tabroom.com"
            )
            must_scrape = True
    else:
        # Check S3 for the scraped data
        s3_client = boto3.client("s3")
        try:
            scrape_output = json.loads(
                s3_client.get_object(
                    Bucket=os.environ["DATA_BUCKET_NAME"],
                    Key=f"{tournament_id}/scraped_results.json",
                )["Body"].read()
            )
            must_scrape = False
        except s3_client.exceptions.NoSuchKey:
            logging.info("No scraped results found in S3. Scraping tabroom.com")
            must_scrape = True
    if must_scrape:
        scrape_output = tabroom_scrape.main(
            tournament_id=tournament_id,
            scrape_entry_records=scrape_entry_records_bool,
            chrome_options=options,
            chrome_service=service,
        )
        save_scraped_results(scrape_output, tournament_id)
    scraped_results = scrape_output["results"]
    name_to_school_dict = scrape_output["name_to_school_dict"]
    code_to_name_dict = scrape_output["code_to_name_dict"]
    name_to_full_name_dict = scrape_output["name_to_full_name_dict"]
    entry_counter_by_school = scrape_output["entry_counter_by_school"]
    school_set = scrape_output["school_set"]
    state_set_list = scrape_output["state_set"]
    school_short_name_dict = scrape_output["school_short_name_dict"]

    # WALK THROUGH EACH EVENT AND PARSE RESULTS
    data_labels = [
        "event_name",
        "event_type",
        "result_set",
        "entry_name",
        "school_name",
        "rank",
        "place",
        "percentile",
        "results_by_round",
    ]
    tournament_results = []
    entry_id_to_entry_code_dictionary = {}
    entry_id_to_entry_entry_name_dictionary = {}
    has_speech = False
    has_debate = False
    for category in response_data["categories"]:
        for event in category["events"]:
            # Create dictionaries to map the entry ID to an Entry Code and Entry Name
            # This only looks at the first round of the event -- theoretically that could be a problem for late adds
            update_global_entry_dictionary(
                sections=event.get("rounds", [{}])[0].get("sections", []),
                code_dictionary=entry_id_to_entry_code_dictionary,
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
            )
            # Parse the result set and get its important info
            (
                event_is_speech,
                event_is_debate,
                results_data_from_event,
            ) = parse_result_sets(
                event=event,
                entry_id_to_entry_code_dictionary=entry_id_to_entry_code_dictionary,
                entry_id_to_entry_entry_name_dictionary=entry_id_to_entry_entry_name_dictionary,
                name_to_school_dict=name_to_school_dict,
                scraped_results=scraped_results,
            )
            # Update long-lived variables with the data
            has_speech = has_speech or event_is_speech
            has_debate = has_debate or event_is_debate
            tournament_results += results_data_from_event

    # Check if a result name has a 'full name' in the full name dictionary (scraped from Tabroom.com)
    # If it exists, replace the short name with the full name
    # Full name can only be ascertained from web scraping
    if scrape_entry_records_bool:
        for result in tournament_results:
            if result["entry_name"] in name_to_full_name_dict:
                result["entry_name"] = name_to_full_name_dict[result["entry_name"]]

    # Select the schools to write up reports on
    if all_schools:
        schools_to_write_up = school_set
        grouped_data = group_data_by_school(
            school_short_name_dict=school_short_name_dict,
            results=tournament_results,
            all_schools=all_schools,
        )
    else:
        schools_to_write_up = set([school_name])
        grouped_data = group_data_by_school(
            school_short_name_dict=school_short_name_dict,
            results=tournament_results,
            school_name=school_name,
        )
    # Generate a school-keyed dict of all the GPT prompts and responses for each school
    # Use the school SHORTNAME as the key
    all_schools_dict = generate_chat_gpt_paragraphs(
        tournament_data=response_data,
        custom_url=custom_url,
        school_count=len(school_set),
        state_count=len(state_set_list),
        has_speech=has_speech,
        has_debate=has_debate,
        entry_dictionary=name_to_school_dict,
        context=context,
        schools_to_write_up=schools_to_write_up,
        grouped_data=grouped_data,
        percentile_minimum=percentile_minimum,
        max_results_to_pass_to_gpt=max_results_to_pass_to_gpt,
        read_only=read_only,
        data_labels=data_labels,
        school_short_name_dict=school_short_name_dict,
        judge_map=scrape_output["judge_map"],
        open_ai_key_path=open_ai_key_path,
        open_ai_key_secret_name=open_ai_key_secret_name,
    )
    # return a dictionary of schools with the summary text and all GPT prompts
    return all_schools_dict


if __name__ == "__main__":
    # Get arguments (no pun intended)
    args = parse_arguments()
    school_name = args.school_name
    tournament_id = args.tournament_id
    all_schools = bool(args.all_schools)
    custom_url = args.custom_url
    read_only = bool(args.read_only)
    percentile_minimum = int(args.percentile_minimum)
    max_results_to_pass_to_gpt = int(args.max_results)
    context = args.context
    scrape_entry_records_bool = bool(args.scrape_entry_records_bool)
    if args.open_ai_key_path:
        open_ai_key_path = args.open_ai_key_path
        open_ai_key_secret_name = None
    else:
        open_ai_key_secret_name = args.open_ai_key_secret_name
        open_ai_key_path = None
    main(
        school_name=school_name,
        tournament_id=tournament_id,
        all_schools=all_schools,
        custom_url=custom_url,
        read_only=read_only,
        percentile_minimum=percentile_minimum,
        max_results_to_pass_to_gpt=max_results_to_pass_to_gpt,
        context=context,
        scrape_entry_records_bool=scrape_entry_records_bool,
        open_ai_key_path=open_ai_key_path,
        open_ai_key_secret_name=open_ai_key_secret_name,
    )
