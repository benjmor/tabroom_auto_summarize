import json
import urllib.request
import os
import ssl
from .scraper import tabroom_scrape as tabroom_scrape
from .update_global_entry_dictionary import update_global_entry_dictionary
from .parse_arguments import parse_arguments
from .group_data_by_school import group_data_by_school
from .generate_chat_gpt_paragraphs import generate_chat_gpt_paragraphs
from .parse_result_sets import parse_result_sets


def main(
    school_name: str = "",
    tournament_id: str = "",
    all_schools: bool = False,
    custom_url: str = "",
    read_only: bool = False,
    percentile_minimum: int = 50,
    max_results_to_pass_to_gpt: int = 15,
    context: str = "",
    scrape_entry_records_bool: bool = True,
    open_ai_key_path: str = None,
    open_ai_key_secret_name: str = None,
):
    # DOWNLOAD DATA FROM THE TABROOM API - We'll use a combination of this and scraping
    response = urllib.request.urlopen(  # nosec - uses http
        url=f"http://www.tabroom.com/api/download_data.mhtml?tourn_id={tournament_id}",
        context=ssl._create_unverified_context(),  # nosec - data is all public
    )
    html = response.read()
    data = json.loads(html)

    # SCRAPE TABROOM FOR ALL THE GOOD DATA NOT PRESENT IN THE API
    scrape_output = tabroom_scrape.main(
        tournament_id=tournament_id, scrape_entry_records=scrape_entry_records_bool
    )
    scraped_results = scrape_output["results"]
    name_to_school_dict = scrape_output["name_to_school_dict"]
    code_to_name_dict = scrape_output["code_to_name_dict"]
    name_to_full_name_dict = scrape_output["name_to_full_name_dict"]
    entry_counter_by_school = scrape_output["entry_counter_by_school"]
    school_set = scrape_output["school_set"]
    state_set = scrape_output["state_set"]

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
    for category in data["categories"]:
        for event in category["events"]:
            # Create dictionaries to map the entry ID to an Entry Code and Entry Name
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
            results=tournament_results, all_schools=all_schools
        )
    else:
        schools_to_write_up = set([school_name])
        grouped_data = group_data_by_school(
            results=tournament_results, school_name=school_name
        )

    all_schools_dict = {}
    # FOR EACH SCHOOL, GENERATE A SUMMARY AND SAVE IT TO DISK
    os.makedirs(f"{data['name']}_summaries", exist_ok=True)
    generate_chat_gpt_paragraphs(
        tournament_data=data,
        custom_url=custom_url,
        school_count=len(school_set),
        state_count=len(state_set),
        has_speech=has_speech,
        has_debate=has_debate,
        entry_dictionary=name_to_school_dict,
        header_string="|".join(data_labels),
        context=context,
        schools_to_write_up=schools_to_write_up,
        grouped_data=grouped_data,
        percentile_minimum=percentile_minimum,
        max_results_to_pass_to_gpt=max_results_to_pass_to_gpt,
        read_only=read_only,
        data_labels=data_labels,
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
