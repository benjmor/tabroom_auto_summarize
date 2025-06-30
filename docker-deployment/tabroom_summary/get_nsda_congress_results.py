import json


def parse_this_round_ranks(values):
    """
    Helper function to parse the ranks for a specific round.
    This function extracts the rank values from the provided values list.
    """
    round_results = []
    for value in values:
        if "priority" in value and value["priority"] == 999:
            big_ugly_string = value.get("value", "")
            big_ugly_object = json.loads(big_ugly_string)
            for round_id in big_ugly_object.keys():
                session_scores = big_ugly_object[round_id]["results"]
                for session_score in session_scores.values():
                    if "rank" in session_score:
                        round_results.append(session_score["rank"])
    return round_results


def get_nsda_congress_results(
    event,
    code_dictionary,
    entry_dictionary,
    entry_to_school_dict,
    scraped_data,
):
    """
    Function for parsing NSDA Congress results.
    This function should be implemented to fetch and process the results
    for NSDA Congress events.

    NSDA Congress is unique in that it has multiple chambers,
    and scores from each chamber are calculated independently.
    That is, each round is a clean slate.
    """
    ret_val = {}
    total_entries = 0
    round_names = ["Prelim", "Qtr", "Sem", "Final"]
    for round_name in round_names:
        # Logic here is to use prelims to start and continually update if a student advances to subsequent rounds.
        results_by_round = [
            r_set
            for r_set in event.get("result_sets", [])
            if r_set.get("label", "").startswith(round_name)
        ]
        if not results_by_round:
            continue

        # The rank string is interesting here. The total number of entries is easy, but the overall place is basically extrapolated from the student's rank in the chamber
        total_entries = max(total_entries, len(results_by_round[0]["results"]))
        # This is such a hack, but I will blame Palmer for mid data.
        number_of_chambers = 0
        for result_thingamajig in results_by_round[0]["results"]:
            if (
                result_thingamajig["rank"] == 1
            ):  # number of chambers is the number of first place results
                number_of_chambers += 1

        for result_set in results_by_round[0]["results"]:
            entry_code = result_set["entry"]
            entry_name = entry_dictionary[entry_code].replace("  ", " ").strip()
            place = ((int(result_set.get("place")) - 1) * number_of_chambers) + 1
            rank_string = f"{place}/{total_entries}"
            round_by_round_results_this_round = parse_this_round_ranks(
                result_set["values"]
            )
            try:
                results_by_round_all_rounds = json.loads(
                    ret_val[entry_code]["results_by_round"]
                )
                results_by_round_all_rounds[round_name] = (
                    round_by_round_results_this_round
                )

            except KeyError:
                results_by_round_all_rounds = {}
                results_by_round_all_rounds[round_name] = (
                    round_by_round_results_this_round
                )

            ret_val[entry_code] = {
                "event_name": event["name"],
                "event_type": "Congress",
                "result_set": "Final Places",
                "entry_name": entry_name,
                "entry_code": entry_code,
                "school_name": entry_to_school_dict[entry_name],
                "rank": rank_string,
                "total_entries": total_entries,
                "round_reached": round_name,
                "percentile": int(
                    float(100 - ((100 * place) / total_entries))
                ),  # Percentile is calculated based on the place
                "place": place,
                "results_by_round": json.dumps(results_by_round_all_rounds),
            }

    ret_list = []
    for entry_code, result in ret_val.items():
        ret_list.append(result)

    return ret_list
