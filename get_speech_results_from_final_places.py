import logging
import re


def get_speech_results_from_final_places(
    # Results array from the event's Final Places page
    final_results_result_set: dict,
    # Name of the speech event
    event_name: str,
    # Filters data to just top performances (80%ile) and school-specific performances
    filtered: bool,
    ENTRY_DICTIONARY,
    ENTRY_TO_SCHOOL_DICT_GLOBAL,
    PERCENTILE_MINIMUM,
    # Name of the school, if filtering results
    school_name: str = "",
):
    """
    Assumes there is a Final Places result published for a speech event.
    Returns a list of pipe-delimited strings with results to append to the ChatGPT prompt.
    """
    ret_val = []
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
