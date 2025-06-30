import json
import logging


def get_ranks_by_round_from_nsda_result_sets(
    nsda_speech_results_sets: list[dict],
):
    ranks_by_round_dict = {}
    ranks_by_round_result_set = [
        result_set
        for result_set in nsda_speech_results_sets
        if result_set.get("label", "") == "All Rounds"
    ][0].get("results", {})
    for result in ranks_by_round_result_set:
        if "entry" not in result:
            continue
        entry_code = result["entry"]
        if entry_code not in ranks_by_round_dict:
            ranks_by_round_dict[entry_code] = {}
        round_results = {}
        for round_result in result.get("values", []):
            if "value" not in round_result:
                continue  # Student did not compete in this round
            round_results[round_result["priority"]] = round_result["value"]
        ranks_by_round_dict[entry_code] = round_results
    return ranks_by_round_dict


def get_speech_prelims_from_nsda_result_sets(
    nsda_speech_results_sets,
    event_name,
    entry_dictionary,
    entry_to_school_dict,
):
    ret_val = []
    ranks_by_round_dict = get_ranks_by_round_from_nsda_result_sets(
        nsda_speech_results_sets,
    )

    prelim_seeds_result_set = [
        result_set
        for result_set in nsda_speech_results_sets
        if result_set.get("label", "") == "Prelim Seeds"
    ][0].get("results", {})
    total_entries = len(prelim_seeds_result_set)
    for result in prelim_seeds_result_set:
        if "entry" not in result:
            logging.error(
                f"Could not find 'entry' in result {result} for {event_name}. Skipping."
            )
            continue
        entry_code = result["entry"]
        entry_name = (
            entry_dictionary[entry_code].replace("  ", " ").strip()
        )  # Remove double space names
        try:
            ranks_by_round_dict[entry_code]
        except KeyError:
            logging.error(
                f"Could not find {entry_code} in ranks_by_round_dict for {event_name}. Skipping."
            )
            continue
        ret_val.append(
            {
                "event_name": event_name,
                "event_type": "speech",
                "result_set": "Prelim Results",
                "entry_name": entry_name,
                "entry_code": entry_code,
                "school_name": entry_to_school_dict[entry_name],
                "rank": f"{result["rank"]}/{total_entries}",
                "round_reached": len(ranks_by_round_dict[entry_code]),
                "percentile": result["percentile"],
                "place": result["rank"],
                "results_by_round": json.dumps(ranks_by_round_dict[entry_code]),
            }
        )
    return ret_val
