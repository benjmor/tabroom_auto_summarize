import logging
import re


# TODO - HANDLE TIES: list all tied schools; rivals are above/below the tie group
def get_sweepstakes_string(
    sweepstakes_data,
    school_name,
    school_count,
):
    # The sweepstakes key is a list of school sweepstakes results, each containing a school_name, rank, and points.
    # The list is guaranteed to be sorted by rank.
    # Find position of school_name in the sweepstakes list and return its rank
    tie_exists = False  # TODO - handle cases where there's a tie
    rank = None
    points = None
    winner_school_name = sweepstakes_data[0]["school_name"]
    winner_school_points = sweepstakes_data[0]["points"]
    for index, sweepstakes_result in enumerate(sweepstakes_data):
        if sweepstakes_result["school_name"] == school_name:
            rank = sweepstakes_result["rank"]
            if re.search("-T", rank):
                logging.info(f"Found a tie in sweepstakes for {school_name}!")
                tie_exists = True
            points = sweepstakes_result["points"]
            try:
                better_rival_school = sweepstakes_data[index - 1]["school_name"]
                better_rival_points = sweepstakes_data[index - 1]["points"]
                # If you are at index 0, there is no better rival.
                if index == 0:
                    better_rival_school = None
                    better_rival_points = None
            except IndexError:
                better_rival_school = None
                better_rival_points = None
            try:
                worse_rival_school = sweepstakes_data[index + 1]["school_name"]
                worse_rival_points = sweepstakes_data[index + 1]["points"]
            except IndexError:
                worse_rival_school = None
                worse_rival_points = None
    if not (rank and points):
        logging.error(f"Could not find {school_name} in sweepstakes data!")
        return ""

    sweepstakes_string = f"""
Sweepstakes awards are a team award based on the total points earned by students from each school. In the sweepstakes competition, {school_name} finished as the #{rank} school out of {school_count} total, earning a total of {points} sweepstakes points. The winning school was {winner_school_name}, with {winner_school_points} points.
"""

    if worse_rival_school and worse_rival_points:
        sweepstakes_string += (
            "\n"
            + f"{school_name} finished ahead of their rival school {worse_rival_school}, who earned {worse_rival_points} points."
        )
    if better_rival_school and better_rival_points:
        sweepstakes_string += (
            "\n"
            + f"{school_name} finished behind their rival school {better_rival_school}, who earned {better_rival_points} points."
        )
    if tie_exists:
        pass
    return sweepstakes_string
