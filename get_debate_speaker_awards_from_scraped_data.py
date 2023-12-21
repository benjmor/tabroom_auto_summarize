def get_debate_speaker_awards_from_scraped_data(
    speaker_results: list[dict],
    event_name,
    event_entries=0,
) -> list[dict]:
    """
    Returns a list of result objects to be consumed by ChatGPT
    """
    ret_val = []
    total_entries = max(event_entries, len(speaker_results))

    for speaker_result in speaker_results:
        # Remove tiebreaks
        place_no_tiebreak = speaker_result["place"].replace("-T", "")
        ret_val.append(
            {
                "event_name": event_name,
                "event_type": "debate",
                "result_set": "Speaker Awards",
                "entry_name": speaker_result["name"],
                "entry_code": speaker_result["code"],
                "school_name": speaker_result["school"],
                "rank": f"{place_no_tiebreak}/{total_entries}",
                "round_reached": "N/A",
                "percentile": int(100 - (100 * int(place_no_tiebreak) / total_entries)),
                "results_by_round": speaker_result["round_by_round"],
            }
        )
    return ret_val
