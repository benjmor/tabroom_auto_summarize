import logging
import re


def get_speech_results_from_final_places(
    # Results array from the event's Final Places page
    final_results_result_set: dict,
    # Name of the speech event
    event_name: str,
    entry_dictionary,
    entry_to_school_dict,
    event_entry_count_override: int = None,  # TODO - pass this value
):
    """
    Assumes there is a Final Places result published for a speech event.
    Returns a list of pipe-delimited strings with results to append to the LLM prompt.
    """
    ret_val = []
    unique_entries = set()
    for result in final_results_result_set:
        if "entry" not in result:
            logging.error(
                f"Could not find 'entry' in result {result} for {event_name}. Skipping."
            )
            continue
        unique_entries.add(result["entry"])
    if event_entry_count_override is not None:
        unique_entry_count = event_entry_count_override
    else:
        unique_entry_count = len(
            unique_entries
        )  # if the final places result set is truncated, this will be inaccurate. Fix by passing an override value.
    current_implicit_place_value = 0
    for result in final_results_result_set:
        # Check if the values is a dummy value, continue if it is.
        if not result["values"][0]:
            continue
        current_implicit_place_value += 1
        try:
            entry_name = entry_dictionary[result["entry"]].strip()  # Remove whitespace
        except KeyError:
            logging.error(
                f"Could not find entry name for {result['entry']} in the entry dictionary in event {event_name}. Skipping. This may be due to a late add or potentially a round 1 bye."
            )
            continue
        entry_code = ""  # CODE_DICTIONARY["entry"] # This is honestly pretty useless for speech, will omit.
        try:
            entry_school = entry_to_school_dict[entry_name]
        except KeyError:
            logging.error(
                f"Could not find {entry_name} in ENTRY_TO_SCHOOL_DICT_GLOBAL."
            )
            entry_school = "UNKNOWN"
        rank = result["rank"]
        try:
            place = int(result["place"])
        except (ValueError, TypeError, KeyError):
            place = current_implicit_place_value
        try:
            percentile = result["percentile"]
        except KeyError:
            percentile = int(100.0 * (1 - (place - 1) / unique_entry_count))
        # Palmer likes to hide round-by-round results in this very low-priority column.
        # Might as well include it to give a summary of how each round went.
        ranks_by_round = ""
        for value in result["values"]:
            if value["priority"] == 999:
                if "value" in value:
                    ranks_by_round = value["value"]
                else:
                    ranks_by_round = "N/A"
                break
        ret_val.append(
            {
                "event_name": event_name,
                "event_type": "speech",
                "result_set": "Final Places",
                "entry_name": entry_name,
                "entry_code": entry_code,
                "school_name": entry_school,
                "rank": f"{rank}/{unique_entry_count}",
                "round_reached": place,
                "percentile": percentile,
                "place": result["rank"],
                "results_by_round": ranks_by_round,
            }
        )
    # Return the results sorted with best-percentile results at the top, so the LLM focuses on those
    return ret_val
