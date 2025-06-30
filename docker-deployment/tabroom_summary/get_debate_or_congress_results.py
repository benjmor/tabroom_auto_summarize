import json
import logging
import re
from .get_debate_speaker_awards_from_scraped_data import (
    get_debate_speaker_awards_from_scraped_data,
)


def get_ranked_ret_val(ret_val):
    # Sort the ret val based on the round_reached field, then by the number of Ws in the results_by_round field
    # Shard the data by the result_set type
    # and then sort each shard by round_reached and number of Ws
    shards = {}
    for result in ret_val:
        result_set = result["result_set"]
        if result_set not in shards:
            shards[result_set] = []
        shards[result_set].append(result)

    for result_set, results in shards.items():
        if results[0].get("place", "N/A") != "TBD":
            continue  # If all places are known, no need to rank
        results.sort(
            key=lambda x: (
                int(x.get("round_reached", 0)),
                x.get("results_by_round", "").count("W"),
            ),
            reverse=True,  # Sort by round_reached descending, then by Ws descending
        )
        # Assign ranks based on the sorted order
        for index, single_result in enumerate(results):
            single_result["rank"] = f"{index + 1}/{len(results)}"
            single_result["place"] = index + 1
            single_result["percentile"] = int(
                100 - ((100 * (index + 1)) / len(results))
            )

    # Put the shards back together
    ret_val = []
    for result_set, results in shards.items():
        ret_val.extend(results)
    return ret_val


def get_debate_or_congress_results(
    # Event dictionary from the Tabroom data
    event: dict,
    entry_to_school_dict: dict,
    code_dictionary,
    entry_dictionary,
    scraped_data: list[dict],
    event_type: str = "debate",  # debate or congress
):
    """
    Used for parsing Debate results data.

    Takes in an event and returns a list of objects containing results data.
    Each object represents an individual result (eg. speaker points ranking, final place, etc)
    """
    ret_val = []
    event_name = event["name"]
    total_entries = 0
    for r_set in event.get("result_sets", []):
        if "results" not in r_set:
            continue  # Skip empty result sets
        if r_set.get("bracket") == 1:
            continue  # No brackets for now -- doesn't translate well to text
            # TODO - would be fun to tell you who a team faced in the bracket, but not a priority right now.
        # Get total entry count
        if r_set["label"] != "Speaker Awards":
            try:
                # Get the total number of entries in the result set
                # TODO - if a results set only has part of the entries, we would need a different source for the total entries.
                total_entries = max(
                    total_entries,
                    len(
                        r_set["results"],
                    ),
                )
            except:
                pass  # If we can't get the total entries, skip it

        # Take action based on the type of result set
        label = r_set["label"]
        # Separate function to handle speaker awards.
        if label == "Speaker Awards":
            for scraped_event in scraped_data:
                if scraped_event["event_name"] == event_name:
                    for scraped_result_set in scraped_event["result_list"]:
                        if not scraped_result_set:
                            continue
                        if scraped_result_set["result_set_type"] == "Speaker Awards":
                            speaker_award_results = (
                                get_debate_speaker_awards_from_scraped_data(
                                    speaker_results=scraped_result_set["results"],
                                    event_name=event_name,
                                    event_entries=total_entries,
                                )
                            )
                            for spk_result in speaker_award_results:
                                ret_val.append(spk_result)
            # Skip the rest of the logic -- all speaker point data is handled in function
            continue
        elif (
            re.search(r"NDCA Dukes and Bailey Points", label)
            or re.search(r"NDCA Baker Points", label)
            or re.search(r"NDCA Averill Points", label)
        ):
            # These points are some real inside baseball that no one cares about
            continue
        for result in r_set["results"]:
            if result["values"] == [{}]:
                total_entries -= (
                    1  # Adjust blank entry values here as they mess up the numbers
                )
        for result in r_set["results"]:
            if "entry" not in result:
                continue  # Handling a strange case for blank results
            if result["values"] == [{}]:
                continue  # Sometimes Palmer populates a duplicate entry with blank 'values'. Skip it.
            results_by_round = ""  # Palmer likes to hide round-by-round results in this very low-priority column.
            if label == "All Rounds":
                list_of_round_results = []
                last_round_was_blank = False
                for value in result["values"]:
                    if value.get("value", ""):
                        if last_round_was_blank:
                            # If the last round was blank, add a bye for it
                            list_of_round_results.append("B")
                            last_round_was_blank = False
                        list_of_round_results.append(value["value"])
                    else:
                        last_round_was_blank = True
                results_by_round = ", ".join(list_of_round_results)
            else:
                for value in result["values"]:
                    if "priority" not in value:
                        continue
                    if value["priority"] == 999:
                        results_by_round = value.get("value", "")
                    # Stash the bid type in the results_by_round field
                    if label == "TOC Qualifying Bids" and value["priority"] == 1:
                        results_by_round = value["value"]

            try:
                entry_name = entry_dictionary[result["entry"]]
                entry_code = code_dictionary[result["entry"]]
            except KeyError:
                logging.warning(
                    f"Could not find entry name or code for {result['entry']}. Skipping."
                )
                continue
            rank = result.get("rank", "TBD")
            round_reached = (
                len(results_by_round.split(","))
                if label == "All Rounds"
                else result.get("place", "N/A")
            )
            result_school = result.get(
                "school", entry_to_school_dict.get(entry_name, "UNKNOWN")
            )
            # Try to get the percentile, but if it's not there, calculate it
            try:
                percentile = result["percentile"]
            except KeyError:
                try:
                    percentile = 100 - ((100 * float(rank)) / float(total_entries))
                except:
                    percentile = 0  # If we can't calculate it, just set it to 0

            # Treat TOC bids as 100th percentile! It's a big achievement.
            rank_string = f"{rank}/{total_entries}"
            if label == "TOC Qualifying Bids":
                percentile = 100
                rank_string = "N/A"
            ret_val.append(
                {
                    "event_name": event_name,
                    "event_type": event_type,
                    "result_set": label,
                    "entry_name": entry_name,
                    "entry_code": entry_code,
                    "school_name": result_school,
                    "rank": rank_string,
                    "total_entries": total_entries,
                    "round_reached": round_reached,
                    "percentile": percentile,
                    "place": rank,
                    "results_by_round": results_by_round,
                }
            )
    # If any placement is TBD, we need to rank the results
    for instance in ret_val:
        if instance.get("place", "N/A") == "TBD":
            return get_ranked_ret_val(ret_val)
    else:
        return ret_val


if __name__ == "__main__":
    with open("example_debate_event_data.json", "r") as json_file:
        example_event = json.load(json_file)
    example_entry_to_school_dict = {
        "Cruz & Ward": "Ronald Reagan",
        "Kenadee Donald": "Rufus King",
        "Martin-Caldwell & Elliott": "Rufus King",
        "Rojas & Thiam": "Ronald Reagan",
        "Lucy Wu": "Whitefish Bay",
        "Dakota Gunnare": "West Bend",
        "Elyse Reedell": "West Bend",
        "Noah Mintie": "West Bend",
        "William Mukana": "Marquette",
        "Charles Hamm": "Sheboygan South",
        "Michael Mavity Maddalena": "Sheboygan South",
        "Vidal Ojeda": "Marquette",
        "James Pienkos": "Marquette",
        "Malina Troicki": "Whitefish Bay",
        "Isaac Neumann": "Marquette",
        "Joshua Wilder": "Marquette",
        "Adee Niljikar": "Brookfield Central",
        "Liliana Espinosa": "Homestead",
        "Grant Young": "Marquette",
        "Safiya Quryshi": "Homestead",
        "Simra Jamal": "Whitefish Bay",
        "James Harris": "Whitefish Bay",
        "Aayeshah Singh": "Homestead",
        "Lankella & Riley": "Vel Phillips Memorial",
        "Gehrenbeck & Guerra": "Fort Atkinson",
        "Calvert Minor & Szabo": "Fort Atkinson",
        "Rao & Perez Ayala": "Fort Atkinson",
        "Jerin & Kandukuri": "Middleton",
        "Bernstein & Garcete": "Madison West",
        "Kim & Yu": "Middleton",
        "Flores Lanzo & Nelson": "Middleton",
        "Bruce & Buelling": "Edgewood",
        "Fonseca & Perez-Reyes": "Marquette",
        "Reichert & Hoover": "Fort Atkinson",
        "Posard & Hoagland": "Whitefish Bay",
        "Austin & Oates": "Whitefish Bay",
        "Albiter & Kim": "Middleton",
        "Joel Cho": "Madison West",
        "Bradley & Hope": "Edgewood",
        "Ubell & Shafiq": "Marquette",
        "Riedlinger & Tidberg": "Fort Atkinson",
        "Bugni & Eckstein": "Edgewood",
        "Sieun (Michelle) Lee": "Middleton",
        "Brad Koeller": "Middleton",
        "Chilakapati & Dileep": "Middleton",
        "Boyden & Li": "Whitefish Bay",
        "Bonlender & Hubert": "West Bend",
    }
    example_code_dictionary = {
        "5299296": "Ronald Reagan WC",
        "5304538": "Rufus King KD",
    }
    example_entry_dictionary = {"5299296": "Cruz & Ward", "5304538": "Kenadee Donald"}
    with open("example_scraped_debate_data.json", "r") as json_scraped_file:
        example_scraped_data = json.load(json_scraped_file)
    print(
        json.dumps(
            get_debate_or_congress_results(
                # Event dictionary from the Tabroom data
                event=example_event,
                entry_to_school_dict=example_entry_to_school_dict,
                code_dictionary=example_code_dictionary,
                entry_dictionary=example_entry_dictionary,
                scraped_data=example_scraped_data,
            ),
            indent=4,
        )
    )
