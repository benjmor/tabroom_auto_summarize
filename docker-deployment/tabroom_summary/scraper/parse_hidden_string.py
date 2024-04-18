import re
import json


def parse_hidden_string(hidden_csv_string: str):
    # Define a regular expression pattern to extract round information
    # Starts with R followed by a digit
    # Then a series of pipe-delimited ranks
    # Optionally at the end there is a parentheses-enclosed value
    # Abandon all hope ye who attempt to debug this regex.
    hidden_csv_string = hidden_csv_string.strip()
    round_by_round_results = []
    current_round = 1
    done = False
    while not done:
        this_identifier = "R" + str(current_round)
        next_identifier = "R" + str(current_round + 1)
        # Get the content between the current and next identifier
        try:
            content = re.search(
                f"{this_identifier}.*{next_identifier}", hidden_csv_string
            )[0]
            content = content.replace(this_identifier, "").replace(next_identifier, "")
        # No results for the next round identifier? We're done -- wrap up on this loop!
        except (IndexError, TypeError):
            content = re.search(f"{this_identifier}.*", hidden_csv_string)[0]
            content = content.replace(this_identifier, "").replace(next_identifier, "")
            done = True
        # If it contains an R, something went wrong
        if "R" in content:
            raise Exception("ERROR - Weird result! Did this skip a round or something?")
        ranks_list = content.split("|")[0:-1]
        if len(ranks_list) == 1:
            total_rank = ranks_list[0]
        else:
            # Remove parens from total rank
            total_rank = content.split("(")[1].replace(")", "")
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
    hidden_csv_string = "R12|R21|R31|R41|R53|3|5|(11)R61|1|1|2|2|(7)"
    print(
        json.dumps(
            parse_hidden_string(hidden_csv_string),
            indent=2,
        )
    )
