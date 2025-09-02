import unicodedata
import re


def get_parsed_speaker_points(round_by_round: str) -> str:
    if len(round_by_round) == 0:
        return "N/A"
    all_rounds = round_by_round.split(",")
    parsed_points = []
    for round in all_rounds:
        # We're trying to find scenarios in which there are multiple judges in a round and fix them
        # 2928 is a two judge round, but 29.75 is a single judge round
        # If there are two decimals, or the number is greater than 100, or there are more than 4 digits in the round, it's a two judge round

        # remove any win-loss indicators and just keep numbers and decimal points
        round = re.sub(r"[^\d.]", "", round)
        if len(round) == 0:
            continue

        if (
            len(round.split(".")) == 3
            or float(round) > 100
            or len(round.replace(".", "")) > 4
        ):
            # Find the first score and the second score
            if round[2] == ".":
                first_score = round[:2]
                second_score = round[3:]
            else:
                first_score = round[:1]
                second_score = round[2:]
            # Return the scores in a more readable format
            parsed_points.append(f"{first_score} & {second_score}")
    return ", ".join(parsed_points)


def get_debate_speaker_awards_from_scraped_data(
    speaker_results: list[dict],
    event_name,
    event_entries=0,
) -> list[dict]:
    """
    Returns a list of result objects to be consumed by LLM
    """
    ret_val = []
    total_entries = max(event_entries, len(speaker_results))

    for speaker_result in speaker_results:
        # TODO - if multiple judges in a round, parse the speaker points given better.
        parsed_speaker_points = get_parsed_speaker_points(
            speaker_result["round_by_round"]
        )
        # Skip the entry if we don't know their school
        if "school" not in speaker_result:
            continue
        # Remove tiebreaks
        place_no_tiebreak = speaker_result["place"].replace("-T", "")
        # Get entry code if it exists, otherwise N/A
        try:
            entry_code = speaker_result["code"]
        except:
            entry_code = "N/A"

        ret_val.append(
            {
                "event_name": event_name,
                "event_type": "debate",
                "result_set": "Speaker Awards",
                "entry_name": "".join(
                    [
                        c
                        for c in unicodedata.normalize("NFD", speaker_result["name"])
                        if not unicodedata.combining(c)
                    ]
                ),
                "entry_code": entry_code,
                "school_name": speaker_result["school"],
                "rank": f"{place_no_tiebreak}/{total_entries}",
                "round_reached": "N/A",
                "percentile": int(100 - (100 * int(place_no_tiebreak) / total_entries)),
                "place": place_no_tiebreak,
                "results_by_round": parsed_speaker_points,
            }
        )
    return ret_val
