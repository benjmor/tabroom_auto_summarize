import logging
import re


def get_debate_results_from_rounds_only(
    # Event dictionary from the Tabroom data
    event: dict,
    # Dictionary of entries
    entry_dictionary: dict,
    # Dictionary of codes
    code_dictionary: dict,
    # Map of what school each entry is from
    entry_to_school_dict: dict,
):
    """
    Assumes that the data is for a tournament that only publishes round results, not a 'Final Places' result.
    Returns a list result objects to append to the LLM prompt

    This data is much harder to process than result_sets and may be inaccurate.
    """
    ret_val = []
    event_name = event["name"]
    round_count = len(
        event.get("rounds", [])
    )  # TODO - assumes students competed every round
    overall_scoring = {}
    for round in event.get("rounds", []):
        label = round.get(
            "label", round.get("name", "")
        )  # Fall back to name if no label
        logging.debug(f"Parsing results from event {event_name} round {label}...")
        if "sections" not in round:
            logging.error(
                f"No sections found in event {event_name} round {label}, skipping."
            )
            continue

        for section in round["sections"]:
            logging.debug(
                f"Parsing results from section {section['letter']} in event {event_name} round {label}..."
            )
            for ballot in section["ballots"]:
                # Get winloss
                did_student_win_round = None
                try:
                    did_student_win_round = [
                        score["value"]
                        for score in ballot["scores"]
                        if score["tag"] == "winloss"
                    ][0]
                except (KeyError, IndexError):
                    # Treat nonexistent scores like forfeits for now, unless bye
                    if ballot["entry"] == "bye":
                        did_student_win_round = 1
                    # Congress will also land here -- you can't really win or lose a congress round so it's ok
                    else:
                        did_student_win_round = 0

                # Get speaker point values (TODO - check how these get associated in PF)
                try:
                    points = [
                        score["value"]
                        for score in ballot["scores"]
                        if score["tag"] == "points"
                    ][0]
                except Exception:
                    points = ""

                # Get student info (name/code)
                try:
                    entry_name = entry_dictionary[ballot["entry"]]
                except KeyError:
                    logging.error(
                        f"Could not find entry {ballot['entry']} in the global entry dictionaries, attempting to pull from ballot directly. This may be the result of a bye or late-add."
                    )
                    try:
                        entry_name = ballot["entry_name"]
                    except Exception:
                        logging.error(
                            f"Could not find entry {ballot['entry']}, skipping."
                        )
                        continue
                try:
                    entry_code = code_dictionary[ballot["entry"]]
                except KeyError:
                    logging.error(
                        f"Could not find entry {ballot['entry']} in the global entry dictionaries, attempting to pull from ballot directly. This may be the result of a bye or late-add."
                    )
                    try:
                        entry_code = ballot["entry_code"]
                    except Exception:
                        logging.error(
                            f"Could not find entry {ballot['entry']}, skipping."
                        )
                        continue
                entry_school_for_dict = entry_to_school_dict.get(entry_name, "")

                # Add ballot data to student cumulative score
                if not overall_scoring.get(entry_name, ""):
                    overall_scoring[entry_name] = {}
                    overall_scoring[entry_name]["school"] = entry_school_for_dict
                    overall_scoring[entry_name]["code"] = entry_code
                    overall_scoring[entry_name]["score_list"] = []
                    overall_scoring[entry_name]["win_total"] = 0

                if did_student_win_round:
                    result_char = "W"
                else:
                    result_char = "L"
                overall_scoring[entry_name]["score_list"].append(
                    f"Round {round['name']}: {result_char} {points}".strip()
                )
                overall_scoring[entry_name]["win_total"] += did_student_win_round

    overall_scoring_sorted = dict(
        sorted(
            overall_scoring.items(), key=lambda item: item[1]["win_total"], reverse=True
        )
    )
    if len(overall_scoring_sorted) == 0:
        logging.error(
            f"No results found for event {event_name} in the rounds only mode, skipping."
        )
        return ret_val

    # This is a bit of a hack to get the rank of each entry, assuming that all entries with the same win total are tied
    # eg. if 3 entries have 4 wins (in a 4 round tournament), they are all tied for 1st place
    current_entry_rank = 1
    current_win_loss = -1
    for iterator, entry_name in enumerate(overall_scoring.keys(), start=1):
        entry_school = overall_scoring[entry_name]["school"]
        entry_code = overall_scoring[entry_name]["code"]
        loss_count = round_count - overall_scoring[entry_name]["win_total"]
        win_loss = f"{overall_scoring[entry_name]['win_total']}W{loss_count}L"
        # If the win/loss count has changed, update the rank
        if win_loss != current_win_loss:
            current_entry_rank = iterator
            current_win_loss = win_loss
        results_by_round = overall_scoring[entry_name]["score_list"]
        ret_val.append(
            {
                "event_name": event_name,
                "event_type": "debate",
                "result_set": "Final Record",
                "entry_name": entry_name,
                "entry_code": entry_code,
                "school_name": entry_school,
                "rank": f"{current_entry_rank}/{len(overall_scoring_sorted)}",
                "total_entries": len(overall_scoring_sorted),
                "round_reached": "N/A",
                "percentile": 100
                - ((current_entry_rank - 1) * 100 / len(overall_scoring_sorted)),
                "place": win_loss,
                "results_by_round": results_by_round,
            }
        )
    return ret_val


# if __name__ == "__main__":
#     """
#     Testing scenario
#     """
#     get_debate_results_from_rounds_only(
#         event=event,
#         entry_dictionary=entry_dictionary,
#         code_dictionary=code_dictionary,
#         entry_to_school_dict=entry_dictionary,
#     )
