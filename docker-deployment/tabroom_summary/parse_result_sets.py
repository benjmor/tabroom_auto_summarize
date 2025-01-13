from .get_speech_results_from_final_places import get_speech_results_from_final_places
from .get_debate_results_from_rounds_only import get_debate_results_from_rounds_only
from .get_debate_or_congress_results import get_debate_or_congress_results
from .get_speech_results_from_rounds_only import get_speech_results_from_rounds_only
from .get_district_qualifier_results import get_district_qualifier_results
import logging

def parse_result_sets(
    event: dict,
    entry_id_to_entry_code_dictionary: dict,
    entry_id_to_entry_entry_name_dictionary: dict,
    name_to_school_dict: dict,
    scraped_results: dict,
):
    has_debate = False
    has_speech = False
    tournament_results = []
    # Parse results sets
    # Start with District Qualifiers since that's special and processed the same regardless of event type
    for result_set in event.get("result_sets", []):
        # It's way easier to just grab the data from scraped results.
        if result_set["label"] == "District Qualifiers":
            event_name = event["name"]
            scraped_single_event_results_list = [
                result_list
                for result_list in scraped_results
                if result_list.get("event_name", "") == event_name
            ]
            if len(scraped_single_event_results_list) != 1:
                raise ValueError(
                    f"Expected 1 scraped result for event {event_name}, got {len(scraped_single_event_results_list)}"
                )
            scraped_single_event_results = scraped_single_event_results_list[0]
            district_results = get_district_qualifier_results(
                scraped_data=scraped_single_event_results,
                event_name=event.get("name"),
                event_type=event.get("type"),
            )
            for district_result in district_results:
                tournament_results.append(district_result)

    if event["type"] in ["debate", "congress", "wsdc"]:
        has_debate = True
        if "result_sets" not in event:
            debate_round_results = get_debate_results_from_rounds_only(
                code_dictionary=entry_id_to_entry_code_dictionary,
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
                event=event,
            )
            for debate_round_result in debate_round_results:
                tournament_results.append(debate_round_result)
            # Look up the entry in the scraped_data whose name key matches the event name key
            # This is probably horrible, but I don't know where else to make it work.
            scraped_result_for_event = [
                result
                for result in scraped_results
                if result["event_name"] == event["name"]
            ][0]
            if scraped_result_for_event:
                for overall_event_result in scraped_result_for_event["result_list"]:
                    for index, result in enumerate(overall_event_result["results"]):
                        tournament_results.append({
                    "event_name": event["name"],
                    "event_type": event["type"],
                    "result_set": overall_event_result.get("result_set_type", ""),
                    "entry_name": result.get("name", ""),
                    "entry_code": result.get("code", ""),
                    "school_name": result.get("school", ""),
                    "rank": f"{index+1}/{len(overall_event_result["results"])}",
                    "total_entries": len(overall_event_result["results"]),
                    "round_reached": "N/A",
                    "percentile": 100-(100*(index+1)/(len(overall_event_result["results"]))),
                    "results_by_round": f"{result.get("wins", "N/A")} prelim wins",
                })

        else:
            debate_final_results = get_debate_or_congress_results(
                event=event,
                code_dictionary=entry_id_to_entry_code_dictionary,
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
                scraped_data=scraped_results,
                event_type=event["type"],
            )
            for debate_final_result in debate_final_results:
                tournament_results.append(debate_final_result)

        # TODO - add an option to enrich the results via scraped data - perhaps replacing rounds-only?
    elif event["type"] == "speech":
        has_speech = True
        # If Final Places is published as a result set...
        if "Final Places" in [
            result_set.get("label", "") for result_set in event.get("result_sets", [{}])
        ]:
            # Then grab that result set and pass it to the designated parsing function
            logging.debug(f"Parsing Final Places in {event["name"]}")
            final_results_result_set = [
                result_set
                for result_set in event.get("result_sets", [{}])
                if result_set.get("label", "") == "Final Places"
            ][0].get("results", {})
            speech_final_place_results = get_speech_results_from_final_places(
                final_results_result_set=final_results_result_set,
                event_name=event["name"],
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
            )
            for speech_final_place_result in speech_final_place_results:
                tournament_results.append(speech_final_place_result)

        else:
            speech_rounds_based_results = get_speech_results_from_rounds_only(
                event=event,
                code_dictionary=entry_id_to_entry_code_dictionary,
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
            )
            for speech_rounds_based_result in speech_rounds_based_results:
                tournament_results.append(speech_rounds_based_result)

            # TODO - add an option to enrich the results via scraped data - perhaps replacing rounds-only?

    return has_speech, has_debate, tournament_results
