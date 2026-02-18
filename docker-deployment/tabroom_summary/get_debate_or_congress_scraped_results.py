def get_debate_or_congress_scraped_results(
    event,
    scraped_data,
):
    # Filter the scraped results to find the one that matches the event name
    scraped_single_event_results_list = [
        result_list
        for result_list in scraped_data
        if result_list.get("event_name", "") == event["name"]
    ]
    if len(scraped_single_event_results_list) != 1:
        raise ValueError(
            f"Expected 1 scraped result for event {event['name']}, got {len(scraped_single_event_results_list)}"
        )
    scraped_single_event_results = scraped_single_event_results_list[0]
    debate_or_congress_results = []
    if event["type"] == "congress":
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
                    debate_or_congress_results.append(
                        {
                            "event_name": event["name"],
                            "event_type": event["type"],
                            "result_set": "Final Places",
                            "entry_name": place_result.get(
                                "Entry", "Name Not Found"
                            ),  # Hopefully "entry" is human-readable and not a code
                            "entry_code": place_result.get("code", ""),
                            "school_name": place_result.get(
                                "School", "School Not Found"
                            ),
                            "rank": f"{index+1}/{len(result['results'])}",
                            "total_entries": len(result["results"]),
                            "round_reached": len(
                                place_result.get("round_by_round", [])
                            ),
                            "percentile": 100
                            - (100 * (index + 1) / (len(result["results"]))),
                            "place": str(index + 1),
                            "results_by_round": results_by_round_string,
                        }
                    )
    else:
        # TODO - For now, just handle Prelim seeds for debate scraped results, because I am being lazy.
        pass
    return debate_or_congress_results
