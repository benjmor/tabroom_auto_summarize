import logging
import re


def get_speech_results_from_rounds_only(
    # Event dictionary from the Tabroom data
    event: dict,
    # Filters data to just top performances (80%ile) and school-specific performances
    filtered: bool,
    # Dictionary of entries
    ENTRY_DICTIONARY: dict,
    # Dictionary of codes
    CODE_DICTIONARY: dict,
    # Map of what school each entry is from
    ENTRY_TO_SCHOOL_DICT_GLOBAL: dict,
    # Name of the school, if filtering results
    school_name: str = "",
    # Minimum percentile threshold for including a result
    PERCENTILE_MINIMUM: int = 10,
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
