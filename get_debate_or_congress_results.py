import logging
import re


def get_debate_or_congress_results(
    # Event dictionary from the Tabroom data
    event: dict,
    entry_to_school_dict: dict,
    code_dictionary,
    entry_dictionary,
    event_type: str = "debate",  # debate or congress
):
    """
    Used for parsing Debate results data.

    Takes in an event and returns a list of objects containing results data.
    Each object represents an individual result (eg. speaker points ranking, final place, etc)
    """
    ret_val = []
    event_name = event["name"]
    for r_set in event.get("result_sets", []):
        if r_set.get("bracket") == 1:
            continue  # No brackets -- doesn't translate well to text
        label = r_set["label"]
        if (
            re.search(r"NDCA Dukes and Bailey Points", label)
            or re.search(r"NDCA Baker Points", label)
            or re.search(r"NDCA Averill Points", label)
        ):
            continue  # These points are some real inside baseball that no one cares about
        try:
            total_entries = len(
                r_set["results"]
            )  # TODO - figure out total entries in cases where partial results are published
        except:
            total_entries = 0  # couldn't find the entry count
        for result in r_set["results"]:
            if "entry" not in result:
                continue  # Handling a strange case for blank results
            if result["values"] == [{}]:
                continue  # Sometimes Palmer populates a duplicate entry with blank 'values'. Skip it.
            results_by_round = ""  # Palmer likes to hide round-by-round results in this very low-priority column.
            for value in result["values"]:
                if value["priority"] == 999:
                    results_by_round = value["value"]
                    break
                # Stash the bid type in the results_by_round field
                if label == "TOC Qualifying Bids" and value["priority"] == 1:
                    results_by_round = value["value"]
            if label == "Speaker Awards":
                try:
                    # TODO Try to get the individual student name from the Speaker Awards webpage - API does not have it
                    entry_name = entry_dictionary[result["entry"]]
                except Exception:
                    pass

            else:
                entry_name = entry_dictionary[result["entry"]]
            entry_code = code_dictionary[result["entry"]]
            rank = result.get("rank", "N/A")
            round_reached = result.get("place", "N/A")
            result_school = result.get(
                "school", entry_to_school_dict.get(entry_name, "UNKNOWN")
            )
            percentile = result.get("percentile", "N/A")
            # Treat TOC bids as 100th percentile! It's a big achievement.
            if label == "TOC Qualifying Bids":
                percentile = 100

            ret_val.append(
                {
                    "event_name": event_name,
                    "event_type": event_type,
                    "label": label,
                    "entry_name": entry_name,
                    "entry_code": entry_code,
                    "school_name": result_school,
                    "rank": rank,
                    "total_entries": total_entries,
                    "round_reached": round_reached,
                    "percentile": percentile,
                    "results_by_round": results_by_round,
                }
            )
    return ret_val
