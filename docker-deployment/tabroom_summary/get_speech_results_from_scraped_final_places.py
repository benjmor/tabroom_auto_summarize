def get_speech_results_from_scraped_final_places(
    event_name,
    scraped_results,
):
    # Filter the scraped results to find the one that matches the event name
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
    speech_final_place_results = []
    for result in scraped_single_event_results.get("result_list", []):
        if result.get("result_set_type", "") == "Final Places":
            for index, place_result in enumerate(result.get("results", [])):
                results_by_round_raw = place_result.get("round_by_round", [])
                results_by_round = []
                for each_round in results_by_round_raw:
                    ranks = each_round.get("ranks", [])
                    if len(ranks) > 1:
                        results_by_round.append(f"{{{','.join(ranks)}}}")
                    if len(ranks) == 1:
                        results_by_round.append(ranks[0])
                results_by_round_string = "|".join(results_by_round)
                speech_final_place_results.append(
                    {
                        "event_name": event_name,
                        "event_type": "speech",
                        "result_set": "Final Places",
                        "entry_name": place_result.get(
                            "Entry", "Name Not Found"
                        ),  # Hopefully "entry" is human-readable and not a code
                        "entry_code": place_result.get("code", ""),
                        "school_name": place_result.get("School", "School Not Found"),
                        "rank": f"{index+1}/{len(result['results'])}",
                        "total_entries": len(result["results"]),
                        "round_reached": len(
                            place_result.get("round_by_round", [])
                        ),  # not as cool as "Semis" or "Finals", but better than "N/A"
                        "percentile": 100
                        - (100 * (index + 1) / (len(result["results"]))),
                        "place": str(index + 1),
                        "results_by_round": results_by_round_string,
                    }
                )
    return speech_final_place_results
