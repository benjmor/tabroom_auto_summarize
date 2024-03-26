import re
import logging

"""
This little guy takes a combination of API and scraped data to return a list of district qualifier results
"""


def get_district_qualifier_results(
    scraped_data,
    event_name,
    event_type,
) -> list:
    results_list = []
    try:
        total_entries = len(scraped_data["result_list"][0]["results"])
    except IndexError:
        logging.warning(f"No results for {event_name}")
        return results_list
    for result in scraped_data["result_list"][0]["results"]:
        numeric_place = int(re.sub("[^0-9]", "", result["place"]))
        # TODO - technically, this isn't always accurate, but most qualifiers have <30 entries
        if numeric_place < 3:
            result_set = "District Qualifiers"
        else:
            result_set = "District Alternate"
        result_object = {
            "event_name": event_name,
            "event_type": event_type,
            "result_set": result_set,
            "entry_name": result["name"],
            "entry_code": result["name"],
            "school_name": result["school"],
            "rank": f"{numeric_place}/{total_entries}",
            "total_entries": total_entries,
            "round_reached": "N/A",
            "percentile": 100 - ((numeric_place - 1) * 100 / total_entries),
            "place": "N/A",
            "results_by_round": "",
        }
        results_list.append(result_object)
    return results_list
