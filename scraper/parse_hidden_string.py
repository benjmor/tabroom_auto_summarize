import re
import json


def parse_hidden_string(hidden_csv_string):
    # Define a regular expression pattern to extract round information
    # Starts with R followed by a digit
    # Then a series of pipe-delimited ranks
    # Optionally at the end there is a parentheses-enclosed value
    # Abandon all hope ye who attempt to debug this regex.
    pattern = re.compile(r"(R\d)((\d\|)*)(\(\d+\))?")

    # Find all matches in the input string
    matches = pattern.findall(hidden_csv_string)

    # Initialize the result as a list of dictionaries
    result = []

    # Process each match and construct the JSON structure
    for match in matches:
        round_name = match[0]
        # Ignore the trailing blank entry
        ranks_list = match[1].split("|")[0:-1]
        if len(ranks_list) == 1:
            total_rank = ranks_list[0]
        else:
            # Remove parens from total rank
            total_rank = match[-1].replace("(", "").replace(")", "")

        round_data = {
            "round_name": round_name,
            "total_rank": total_rank,
            "ranks": ranks_list,
        }

        result.append(round_data)

    return result


if __name__ == "__main__":
    hidden_csv_string = "R12|R21|R31|R41|R53|3|5|(11)R61|1|1|2|2|(7)"
    print(
        json.dumps(
            parse_hidden_string(hidden_csv_string),
            indent=2,
        )
    )
