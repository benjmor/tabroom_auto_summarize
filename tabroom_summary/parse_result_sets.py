from .get_speech_results_from_final_places import get_speech_results_from_final_places
from .get_debate_results_from_rounds_only import get_debate_results_from_rounds_only
from .get_debate_or_congress_results import get_debate_or_congress_results
from .get_speech_results_from_rounds_only import get_speech_results_from_rounds_only


def parse_result_sets(
    event: dict,
    entry_id_to_entry_code_dictionary: dict,
    entry_id_to_entry_entry_name_dictionary: dict,
    name_to_school_dict: dict,
    scraped_results: dict,
):
    has_debate = False
    has_speech = False
    # Parse results sets
    if event["type"] in ["debate", "congress"]:
        has_debate = True
        if "result_sets" not in event:
            tournament_results = get_debate_results_from_rounds_only(
                code_dictionary=entry_id_to_entry_code_dictionary,
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
                event=event,
            )
        else:
            tournament_results = get_debate_or_congress_results(
                event=event,
                code_dictionary=entry_id_to_entry_code_dictionary,
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
                scraped_data=scraped_results,
                event_type=event["type"],
            )
        # TODO - add an option to enrich the results via scraped data - perhaps replacing rounds-only?
    elif event["type"] == "speech":
        has_speech = True
        # If Final Places is published as a result set...
        if "Final Places" in [
            result_set.get("label", "") for result_set in event.get("result_sets", [{}])
        ]:
            # Then grab that result set and pass it to the designated parsing function
            final_results_result_set = [
                result_set
                for result_set in event.get("result_sets", [{}])
                if result_set.get("label", "") == "Final Places"
            ][0]["results"]
            tournament_results = get_speech_results_from_final_places(
                final_results_result_set=final_results_result_set,
                event_name=event["name"],
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
            )
        else:
            tournament_results = get_speech_results_from_rounds_only(
                event=event,
                code_dictionary=entry_id_to_entry_code_dictionary,
                entry_dictionary=entry_id_to_entry_entry_name_dictionary,
                entry_to_school_dict=name_to_school_dict,
            )
            # TODO - add an option to enrich the results via scraped data - perhaps replacing rounds-only?

    return has_speech, has_debate, tournament_results
