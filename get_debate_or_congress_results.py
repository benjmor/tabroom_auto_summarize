import json
import logging
import re
from get_debate_speaker_awards_from_scraped_data import (
    get_debate_speaker_awards_from_scraped_data,
)


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
    for r_set in event.get("result_sets", []):
        if r_set.get("bracket") == 1:
            continue  # No brackets for now -- doesn't translate well to text
        label = r_set["label"]
        # Separate function to handle speaker awards.
        if label == "Speaker Awards":
            for scraped_event in scraped_data:
                if scraped_event["event_name"] == event_name:
                    for scraped_result_set in scraped_event["result_list"]:
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
                    results_by_round = value.get("value", "")
                # Stash the bid type in the results_by_round field
                if label == "TOC Qualifying Bids" and value["priority"] == 1:
                    results_by_round = value["value"]

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
                    "result_set": label,
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
