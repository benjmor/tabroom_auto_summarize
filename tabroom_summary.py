# Note: you need to be using OpenAI Python v0.27.0+ for the code below to work, with a
import openai
import argparse
from datetime import datetime
import json
import urllib.request
import logging
import os
import re
import ssl
import tabroom_scrape
import generate_website


ENTRY_DICTIONARY = {}  # Global context
CODE_DICTIONARY = {}
STUDENT_NAME_DICTIONARY = {}
ENTRY_TO_SCHOOL_DICT_GLOBAL = {}
PERCENTILE_MINIMUM = (
    10  # Being a bit generous here -- anyone not in the bottom 10% gets included
)
RESULTS_TO_PASS_TO_GPT = 15
HEADER_STRING = "Event|Event Type|Result Set|Entry Names|Entry Code|School|Rank|Place|Percentile|Results By Round"
SCHOOL_INDEX = HEADER_STRING.split("|").index("School")
EVENT_TYPE_INDEX = HEADER_STRING.split("|").index("Event Type")


def update_global_entry_dictionary(sections):
    # Update entry dictionary by scraping an event's section data
    for section in sections:
        for ballot in section["ballots"]:
            entry_id = ballot["entry"]
            entry_name = ballot["entry_name"]
            entry_code = ballot["entry_code"]
            logging.debug(f"{entry_id}|{entry_name}")
            ENTRY_DICTIONARY[entry_id] = entry_name
            CODE_DICTIONARY[entry_id] = entry_code


def scrape_entries_page():
    """
    This will eventually scrape the entries page to give us an idea of how many students are present and from which states.
    """
    pass


def get_speech_results_from_final_places(
    # Results array from the event's Final Places page
    final_results_result_set: dict,
    # Name of the speech event
    event_name: str,
    # Filters data to just top performances (80%ile) and school-specific performances
    filtered: bool,
    # Name of the school, if filtering results
    school_name: str = "",
):
    """
    Assumes there is a Final Places result published for a speech event.
    Returns a list of pipe-delimited strings with results to append to the ChatGPT prompt.
    """
    ret_val = []
    event_name = event["name"]
    unique_entries = set()
    for result in final_results_result_set:
        unique_entries.add(result["entry"])
    unique_entry_count = len(unique_entries)
    for result in final_results_result_set:
        # Check if the values is a dummy value, continue if it is.
        if not result["values"][0]:
            continue
        entry_name = ENTRY_DICTIONARY[result["entry"]].strip()  # Remove whitespace
        entry_code = ""  # CODE_DICTIONARY["entry"] # This is honestly pretty useless for speech, will omit.
        try:
            entry_school = ENTRY_TO_SCHOOL_DICT_GLOBAL[entry_name]
        except KeyError:
            logging.error(
                f"Could not find {entry_name} in ENTRY_TO_SCHOOL_DICT_GLOBAL."
            )
            entry_school = "UNKNOWN"
        rank = result["rank"]
        place = result["place"]
        percentile = result["percentile"]
        # Palmer likes to hide round-by-round results in this very low-priority column.
        # Might as well include it to give a summary of how each round went.
        ranks_by_round = ""
        for value in result["values"]:
            if value["priority"] == 999:
                ranks_by_round = value["value"]
                break
        is_given_school = re.search(school_name, entry_school) or re.search(
            school_name, entry_code
        )
        if filtered and (
            (float(percentile) < PERCENTILE_MINIMUM)  # Below the threshold
            or not is_given_school
        ):
            continue
        ret_val.append(
            f"{event_name}|speech|Final Places|{entry_name}|{entry_code}|{entry_school}|{rank}/{unique_entry_count}|{place}|{percentile}|{ranks_by_round}"
        )
    # Return the results sorted with best-percentile results at the top, so ChatGPT focuses on those
    return ret_val


def get_speech_results_from_rounds_only(
    # Event dictionary from the Tabroom data
    event: dict,
    # Filters data to just top performances (80%ile) and school-specific performances
    filtered: bool,
    # Name of the school, if filtering results
    school_name: str = "",
):
    """
    Assumes that the data is for a tournament that only publishes round results, not a 'Final Places' result.
    Returns a list of pipe-delimited results strings to append to the ChatGPT prompt

    The string will be a list of individual performances, summarized by their final rank.

    This data is much harder to process than result_sets and may be inaccurate.
    """
    ret_val = []
    event_name = event["name"]
    for round in event.get("rounds", []):
        label = round.get(
            "label", round.get("name", "")
        )  # Fall back to name if no label
        logging.debug(f"Parsing results from event {event_name} round {label}...")
        # For now, only concerned with Finals
        if label == "Finals":
            for section in round["sections"]:
                section_scoring = {}
                logging.debug(
                    f"Parsing results from section {section['letter']} in event {event_name} round {label}..."
                )
                for ballot in section["ballots"]:
                    rank = [
                        score["value"]
                        for score in ballot["scores"]
                        if score["tag"] == "rank"
                    ][0]

                    try:
                        points = [
                            score["value"]
                            for score in ballot["scores"]
                            if score["tag"] == "points"
                        ][0]

                    except Exception:
                        points = 0
                    if not rank:
                        continue
                    try:
                        entry_name = ENTRY_DICTIONARY[ballot["entry"]]
                        entry_code = CODE_DICTIONARY[ballot["entry"]]
                    except KeyError:
                        logging.error(
                            f"Could not find entry {ballot['entry']} in the global entry dictionaries, skipping. This may be the result of a bye or late-add."
                        )
                        continue
                    entry_school_for_dict = ENTRY_TO_SCHOOL_DICT_GLOBAL.get(
                        entry_name, ""
                    )
                    if not section_scoring.get(entry_name, ""):
                        section_scoring[entry_name] = {}
                        section_scoring[entry_name]["school"] = entry_school_for_dict
                        section_scoring[entry_name]["score_list"] = [
                            {"rank": rank, "points": points}
                        ]
                        section_scoring[entry_name]["rank_total"] = rank
                    else:
                        section_scoring[entry_name]["score_list"].append(
                            {"rank": rank, "points": points}
                        )
                        section_scoring[entry_name]["rank_total"] += rank
                # Sort the section_scoring dictionary by rank total
                section_scoring = dict(
                    sorted(
                        section_scoring.items(),
                        key=lambda item: item[1]["rank_total"],
                        reverse=False,
                    )
                )
                for index, (entry_name, scoring) in enumerate(
                    section_scoring.items(), start=1
                ):
                    percentile = (
                        100 * (len(section_scoring) - index + 1) / len(section_scoring)
                    )  # TODO - make this give a competition-wide percentile, based on the field size

                    entry_school = section_scoring[entry_name]["school"]
                    # If filtering, and not in a top percentile or from the specific school, skip
                    is_given_school = re.search(school_name, entry_school) or re.search(
                        school_name, entry_code
                    )
                    if filtered and (
                        (float(percentile) < PERCENTILE_MINIMUM)  # Below the threshold
                        or not is_given_school
                    ):
                        continue
                    ret_val.append(
                        f"{event_name}|speech|{label}|{entry_name}|{entry_code}|{entry_school}|{index}|{index}|{percentile}"
                    )
    return ret_val


def get_debate_results(
    # Event dictionary from the Tabroom data
    event: dict,
    # Filters data to just top performances (80%ile) and school-specific performances
    filtered: bool,
    # Name of the school, if filtering results
    school_name: str = "",
):
    """
    Used for parsing Debate results data.
    Takes in an event and returns a list of pipe-delimited strings with results data
    Each string represents an individual result (eg. speaker points ranking, final place, etc)
    """
    ret_val = []
    event_name = event["name"]
    for r_set in event.get("result_sets", []):
        # TODO - Currently unable to handle bracket data cleanly.
        if r_set.get("bracket") == 1:
            continue
        label = r_set["label"]
        if label == "Final Places":
            total_entries = len(r_set["results"])
        else:
            total_entries = 0
        for result in r_set["results"]:
            if "entry" not in result:
                continue  # Handling a strange case for blank results
            if label == "Speaker Awards":
                try:
                    # Try to get the individual student name from the Speaker Awards
                    # TODO - This needs a lot of work -- probably need to scrape the table not use API
                    entry_name = STUDENT_NAME_DICTIONARY["BLAH"]  # noqa - TODO
                except Exception:
                    # Fall back to parsing the entry dictionary
                    entry_name = ENTRY_DICTIONARY[result["entry"]]
            else:
                entry_name = ENTRY_DICTIONARY[result["entry"]]
            entry_code = CODE_DICTIONARY[result["entry"]]
            rank = (
                f"{result.get('rank')}/{total_entries}"
                if total_entries > 0
                else result.get("rank")
            )
            round_reached = result.get("place")
            result_school = result.get(
                "school", ENTRY_TO_SCHOOL_DICT_GLOBAL.get(entry_name, "UNKNOWN")
            )
            percentile = result.get("percentile", "0")
            if (
                filtered
                and (float(percentile) < PERCENTILE_MINIMUM)
                and (not re.search(school_name, entry_code))
            ):
                continue
            ret_val.append(
                f"{event_name}|debate|{label}|{entry_name}|{entry_code}|{result_school}|{rank}|{round_reached}|{percentile}"
            )
    return ret_val


def generate_chat_gpt_prompt(
    tournament_data, school_name, school_count, custom_url=None
):
    start_date = datetime.strptime(
        tournament_data["start"].split(" ")[0], "%Y-%m-%d"
    ).strftime(
        "%B %d, %Y",
    )  # The start time is useless and inaccurate, just use the date
    if custom_url:
        follow_up_url = custom_url
    else:
        follow_up_url = f"{tournament_data['webname']}.tabroom.com"
    chat_gpt_basic_prompt = f"""
    The following data represents results of a high school speech and debate tournament called {tournament_data["name"]} held in {tournament_data["city"]} ({tournament_data["state"]}), starting on {start_date}.
    
    The tournament was attended by {len(ENTRY_DICTIONARY)} student entries and {school_count} schools.

    Write a 3 paragraph summary for the {school_name} High School newspaper. Use as many student names of {school_name} students as reasonable. Write concisely if there are more than 10 results to write about.
    At the end, indicate that additional information (including how to compete, judge, or volunteer) can be found at {follow_up_url}.
    
    Include individuals' rankings and statistics, such as number of wins. When referencing results, you should include the total number of entries in the event. Don't include raw percentile information in the output.

    Do not use the definite article 'the' before the names of events.
    """
    chat_gpt_debate_prompt = (
        chat_gpt_basic_prompt
        + f"""
    Final Places and Speaker Awards are more important than Prelim seeds. Ignore entries below the {PERCENTILE_MINIMUM}th percentile.

    Wins should be listed earlier than other achievements. Varsity should generally come before Novice or Junior Varsity (JV) results.

    Terms like 'Doubles', 'Octos', and 'Quarters' may be used to indicate the elimination round a team reached.
    Doubles refers to the Round of 32 (also known as double-octofinals), Octos refers to the Round of 16 (octofinals), and Quarters refers to the Round of 8 (quarterfinals), respectively.
    Use these terms to describe the elimination round a debater reached.

    Winning a first place speaker award should be referred to as winning top speaker for the tournament.

    Team entries might be indicated with just last names, and will typically not contain first names. Those teams should be referred to as "the team of", followed by the last names.

    """
    )
    chat_gpt_speech_prompt = (
        chat_gpt_basic_prompt
        + f"""
    Speech events involve acting, prepared speeches, and improvisational speeches.

    Results may include round-by-round results, which represent how a student was ranked in a given room of competition (1 is best). You can reference these when summarizing an individual's performance.

    Some round-by-round results will have multiple scores: these represent scores from a panel of several judges, as opposed to a single judge. If a student receives all 1s from a panel of judges, that can be called out as a "picket fence", which is a positive achievement in speech.
    """
    )

    chat_gpt_payload = [chat_gpt_debate_prompt]
    chat_gpt_payload.append(HEADER_STRING)
    return chat_gpt_payload


if __name__ == "__main__":
    # TODO - Add number of states present if more than 1 into the GPT prompt.

    # PARSE INPUT FROM USER
    parser = argparse.ArgumentParser(
        prog="tabroom_summary",
        description="Uses ChatGPT to create summaries of Tabroom results",
    )
    school_args = parser.add_mutually_exclusive_group(required=True)
    school_args.add_argument(
        "-s",
        "--school-name",
        help="Name of the school that your article will focus on.",
        required=False,
    )
    school_args.add_argument(
        "--all-schools",
        action="store_true",
        help="Generate summaries for all schools in the Tabroom data.",
    )
    parser.add_argument(
        "-t",
        "--tournament-id",
        help="Tournament ID (typically a 5-digit number) of the tournament you want to generate results for.",
        required=True,
    )
    parser.add_argument(
        "--custom-url",
        help="Custom URL of the tournament you want to generate results for. For example, a league website.",
        required=False,
    )
    args = parser.parse_args()
    school_name = args.school_name
    tournament_id = args.tournament_id
    all_schools = args.all_schools
    custom_url = args.custom_url

    # DOWNLOAD DATA FROM THE TABROOM API
    response = urllib.request.urlopen(  # nosec - uses http
        url=f"http://www.tabroom.com/api/download_data.mhtml?tourn_id={tournament_id}",
        context=ssl._create_unverified_context(),  # nosec - data is all public
    )
    html = response.read()
    data = json.loads(html)

    # SCRAPE TABROOM FOR ALL THE GOOD DATA NOT PRESENT IN THE API
    scraped_output, ENTRY_TO_SCHOOL_DICT_GLOBAL = tabroom_scrape.main(
        tournament_id=tournament_id
    )

    # GET THE UNIQUE LIST OF SCHOOLS ATTENDING THE TOURNAMENT
    if all_schools:
        school_set = set()
        for value in ENTRY_TO_SCHOOL_DICT_GLOBAL.values():
            school_set.add(value)
    else:
        school_set = set([school_name])

    # WALK THROUGH EACH EVENT AND PARSE RESULTS
    tournament_results = []
    for category in data["categories"]:
        for event in category["events"]:
            update_global_entry_dictionary(
                sections=event.get("rounds", [{}])[0].get("sections", [])
            )

            # Parse results sets
            if event["type"] == "debate":
                tournament_results += get_debate_results(
                    event=event, filtered=False  # , school_name=school_name
                )
            elif event["type"] == "speech":
                # If Final Places is published as a result set...
                if "Final Places" in [
                    result_set.get("label", "")
                    for result_set in event.get("result_sets", [{}])
                ]:
                    # Then grab that result set and pass it to the designated parsing function
                    final_results_result_set = [
                        result_set
                        for result_set in event.get("result_sets", [{}])
                        if result_set.get("label", "") == "Final Places"
                    ][0]["results"]
                    tournament_results += get_speech_results_from_final_places(
                        final_results_result_set=final_results_result_set,
                        event_name=event["name"],
                        filtered=False,  # , school_name=school_name
                    )
                else:
                    tournament_results += get_speech_results_from_rounds_only(
                        event=event, filtered=False  # , school_name=school_name
                    )

    # FOR EACH SCHOOL, GENERATE A SUMMARY AND SAVE IT TO DISK
    os.makedirs(f"{data['name']}_summaries", exist_ok=True)
    for school in school_set:
        chat_gpt_payload = generate_chat_gpt_prompt(
            tournament_data=data,
            school_name=school,
            custom_url=custom_url,
            school_count=len(school_set),
        )
        filtered_tournament_results = [
            result
            for result in tournament_results
            if result.split("|")[SCHOOL_INDEX] == school
            or (
                result.split("|")[EVENT_TYPE_INDEX] == "debate"
                and result.split("|")[SCHOOL_INDEX][:-3]
                == school  # cut off 2 letter ID
            )
            or (
                False  # TODO - add a case for checking the entry in the school dict directly
            )
        ]
        if not filtered_tournament_results:
            logging.warning(f"No results found for {school}")
            continue
        sorted_filtered_school_results = sorted(
            filtered_tournament_results,
            key=lambda x: float(
                x.split("|")[HEADER_STRING.split("|").index("Percentile")]
            ),
            reverse=True,
        )
        # Filter down to just the top 15 results (based on percentile) to get better results for large schools
        if len(sorted_filtered_school_results) > RESULTS_TO_PASS_TO_GPT:
            top_sorted_filtered_school_results = sorted_filtered_school_results[
                0 : RESULTS_TO_PASS_TO_GPT - 1
            ]
        else:
            top_sorted_filtered_school_results = sorted_filtered_school_results
        logging.info(
            f"School specific results without truncating low percentiles: {sorted_filtered_school_results}"
        )
        chat_gpt_payload += top_sorted_filtered_school_results
        final_gpt_payload = "\r\n".join(chat_gpt_payload)
        openai.api_key_path = "openAiAuthKey.txt"
        logging.info(f"Generating summary for {school}")
        logging.info(f"GPT Prompt: {final_gpt_payload}")
        body_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": final_gpt_payload},
            ],
        )["choices"][0]["message"]["content"]
        headline_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "Generate a headline for the article. The response should be just a single headline",
                },
                {"role": "user", "content": body_response},
            ],
        )["choices"][0]["message"]["content"]
        with open(f"{data['name']}_summaries/{school}_summary.txt", "w") as f:
            f.write(headline_response + "\r\n" + body_response)

    # GENERATE A SIMPLE HTML WEBPAGE WITH THE RESULTS
    generate_website.main(input_directory=f"{data['name']}_summaries")
