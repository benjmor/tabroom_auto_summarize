import re
import json
import logging


def parse_hidden_string(hidden_csv_string: str):
    # Define a regular expression pattern to extract round information
    # Starts with R followed by a digit
    # Then a series of pipe-delimited ranks
    # Optionally at the end there is a parentheses-enclosed value
    # Abandon all hope ye who attempt to debug this regex.
    if not hidden_csv_string:
        return []
    hidden_csv_string = hidden_csv_string.strip()
    round_by_round_results = []
    current_round = 1
    done = False
    no_results_from_previous_round = False
    while not done:
        this_identifier = "R" + str(current_round)
        next_round = str(current_round + 1)
        next_next_round = str(int(next_round) + 1)
        # Get results between the current and next identifier, acknowledging that there may be a BYE resulting in a skipped round
        # Note: Why all this complicated logic? Because R1 matches R10, so need to specify the start/end carefully.
        next_identifier = rf"R[{next_round},{next_next_round}]"
        # Get the content between the current and next identifier
        try:
            content = re.search(
                rf"{this_identifier}.*{next_identifier}", hidden_csv_string
            )[0]
            content = content.replace(this_identifier, "").split("R")[0]
            no_results_from_previous_round = False
        # No results for the next round identifier? We're done -- wrap up on this loop!
        except (IndexError, TypeError):
            try:
                content = re.search(f"{this_identifier}.*", hidden_csv_string)[0]
                content = content.replace(this_identifier, "").split("R")[0]
                done = True
            # If there's no results for even the CURRENT round, then the entry likely had a bye
            except (IndexError, TypeError):
                content = "B|"
                # If we see 2 bye rounds in a row, just finish it
                if no_results_from_previous_round:
                    done = True
                no_results_from_previous_round = True

        # Standardize weird setups
        if content == "BYE":
            content = "B|"
        ranks_list = content.split("|")[0:-1]  # remove the oft-trailing pipe
        if len(ranks_list) == 1:
            # Logic for ranked events (eg. speech) that contain speaker points
            if re.search(r"\d{3,5}", ranks_list[0]):
                if re.search(r"100", ranks_list[0]):
                    total_rank = ranks_list[0][0:-3]
                else:
                    total_rank = ranks_list[0][0:-2]
            else:
                total_rank = ranks_list[0]
        else:
            try:
                # Remove parens from total rank; if points are present after the comma, remove them
                total_rank = content.split("(")[1].replace(")", "").split(",")[0]
                # Remove speaker points from speech events if present
            except IndexError:
                logging.warning("Unable to process total rank from hidden string")
                total_rank = "-1"
        for iterable, rank in enumerate(ranks_list):
            if re.search(r"\d{3,5}", rank):
                if re.search(r"100", rank):
                    ranks_list[iterable] = rank[0:-3]
                else:
                    ranks_list[iterable] = rank[0:-2]
        round_by_round_results.append(
            {
                "round_name": this_identifier,
                "total_rank": total_rank,
                "ranks": ranks_list,
            }
        )
        current_round += 1

    return round_by_round_results


if __name__ == "__main__":
    hidden_csv_string_samples = [
        "R12|R21|R31|R41|R53|3|5|(11)R61|1|1|2|2|(7)",
        "R1L28.0,27.0|(55.0)R3W30.0,30.0|(60.0)R4L|W|L|(1-2)",
        "R1281R2292R3192R421(3)R5153(9)",  # Points for Speech without points in elim rounds
        "R1197|R2198|R3198|R4298|294|195|(5,287)",  # Points for speech with points in elim rounds
    ]
    for hidden_csv_string in hidden_csv_string_samples:
        print(
            json.dumps(
                parse_hidden_string(hidden_csv_string),
                indent=2,
            )
        )
