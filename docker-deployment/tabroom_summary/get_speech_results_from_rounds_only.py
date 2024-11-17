import logging
import re


def get_speech_results_from_rounds_only(
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
    Returns a list of pipe-delimited results strings to append to the LLM prompt

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
            if "sections" not in round:
                logging.warning(
                    f"No 'sections' key found for event {event_name}, round {label}. Skipping."
                )
                continue
            for section in round["sections"]:
                section_scoring = {}
                logging.debug(
                    f"Parsing results from section {section['letter']} in event {event_name} round {label}..."
                )
                for ballot in section["ballots"]:
                    try:
                        rank = [
                            score["value"]
                            for score in ballot[
                                "scores"
                            ] 
                            if score["tag"] == "rank"
                        ][0]
                    except Exception:
                        forfeit_status = ballot.get("forfeit", "false")
                        if forfeit_status == 1:
                            forfeit_status = "true"
                        else:
                            pass
                        logging.warning(
                            f"No 'scores' key found for event {event_name}, round {label}, section {section["id"]}, ballot {ballot["id"]}. This may indicate a forfeit. Forfeit status is {forfeit_status}."
                        )
                        rank = 999 # High value here = forfeit

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
                        entry_name = entry_dictionary[ballot["entry"]]
                        entry_code = code_dictionary[ballot["entry"]]
                    except KeyError:
                        logging.error(
                            f"Could not find entry {ballot['entry']} in the global entry dictionaries, skipping. This may be the result of a bye or late-add."
                        )
                        continue
                    entry_school_for_dict = entry_to_school_dict.get(entry_name, "")
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
                    ret_val.append(
                        {
                            "event_name": event_name,
                            "event_type": "speech",
                            "result_set": "Scoring",
                            "entry_name": entry_name,
                            "entry_code": entry_code,
                            "school_name": entry_school,
                            "rank": index,
                            "round_reached": "N/A",
                            "percentile": percentile,
                            "results_by_round": "N/A",
                        }
                    )
    return ret_val
