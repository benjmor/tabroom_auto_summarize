from datetime import datetime
import re
import logging
import logging
import logging
import logging
from .get_sweepstakes_string import get_sweepstakes_string


def generate_llm_prompt_header(
    tournament_data,
    school_name,
    short_school_name,
    school_count,
    entry_dictionary,
    header_string,
    data_strings,
    default_qualifier_count: int,
    state_count=1,
    has_speech=False,
    has_debate=False,
    context="",
    judge_map={},
):
    """
    Generates a text prompt to send to the LLM, telling it what to create. Does not contain the results, but does contain a data header.

    Just add results data and this baby is ready to send to the LLM.

    Returns a list of strings with LLM prompt pieces.
    """
    start_date = datetime.strptime(
        tournament_data["start"].split(" ")[0], "%Y-%m-%d"
    ).strftime(
        "%B %d, %Y",
    )  # The start time is useless and inaccurate, just use the date
    if state_count > 1:
        state_detail = f" from {state_count} states."
    else:
        state_detail = "."
    if re.search("District Tournament", tournament_data["name"]):
        if default_qualifier_count == 1:
            qualifier_count_string = "the top entry in each event qualifies"
        else:
            qualifier_count_string = f"the top {default_qualifier_count} placing entries in each event qualify"
        # TODO - Be more precise here about how many qualify.
        nsda_context = f"This tournament is an NSDA national qualifier; {qualifier_count_string} to this year's National Speech and Debate Tournament. The remaining competitors are alternate qualifiers in case qualifiers cannot attend Nationals."
    else:
        nsda_context = ""
    # Start with the basic prompt
    chat_gpt_payload_list = [
        f"""The following data represents results of a team's performance at a speech and debate tournament called {tournament_data["name"]} held in {tournament_data["city"]} ({tournament_data["state"]}) on {start_date}. {nsda_context} {context}
    
The tournament was attended by {len(entry_dictionary)} student entries and {school_count} schools{state_detail} Include this context in the article.

Write a 4 paragraph summary for the {school_name} speech and debate team social media feed. Use as many student names of {school_name} students as reasonable. Keep the tone factual, professional, concise, and positive. Avoid commenting on negative results. Selectively include individuals' rankings, wins, and placement out of the total number of entries, but prioritize names and final places. Do not prepend paragraphs with labels like 'Paragraph 1'.

The presence of a "Final Places" result does not mean a student made the final round; it just indicates their overall placement in the tournament. 

ONLY INCLUDE RESULTS FROM THE RESULTS DATA. DO NOT INCLUDE ANY RESULTS THAT DO NOT APPEAR IN RESULT_DATA.
    """
    ]

    # Add sweepstakes results
    if "sweepstakes" in tournament_data:
        logging.info("Found sweepstakes data!")
        sweepstakes_string = get_sweepstakes_string(
            sweepstakes_data=tournament_data["sweepstakes"],
            school_name=short_school_name,
            school_count=school_count,
        )
        chat_gpt_payload_list.append(sweepstakes_string)

    # Thank judges, if published judge list exists
    if judge_map:
        judge_list = ", ".join(judge_map.get(short_school_name, []))
        chat_gpt_payload_list.append(
            f"At the end of the article, thank these individuals for volunteering to judge for the tournament (there wouldn't be a tournament without them!): {judge_list}"
        )

    # Loop through data strings looking to add context if Claude needs to know about debate or speech terms
    found_elims = False
    abbreviation_map = {
        "PF": {
            "present": False,
            "description": "PF is an abbreviation for Public Forum, a 2-on-2 style of debate.",
        },
        "LD": {
            "present": False,
            "description": "LD is an abbreviation for Lincoln-Douglas, a 1-on-1 style of debate.",
        },
        "CX": {
            "present": False,
            "description": "CX is an abbreviation for Cross-examination (aka Policy), a 2-on-2 style of debate.",
        },
    }
    for data_string in data_strings:
        if re.search(data_string, "Doubles|Octos|Quarters|Semis") and not found_elims:
            chat_gpt_payload_list.append(
                f"""'Doubles' refers to the Round of 32 (also known as double-octofinals), 'Octos' refers to the Round of 16 (octofinals), and 'Quarters' refers to the Round of 8 (quarterfinals), respectively. Use these terms to describe the elimination round a debater reached.
            """
            )
            found_elims = True
        for abbreviation in abbreviation_map.keys():
            if (
                abbreviation in data_string
                and not abbreviation_map[abbreviation]["present"]
            ):
                chat_gpt_payload_list.append(
                    abbreviation_map[abbreviation]["description"]
                )
                abbreviation_map[abbreviation]["present"] = True

    # Conditionally add debate context
    if has_debate:
        chat_gpt_payload_list.append(
            f"""Results may include round-by-round results, delimited by a "|" character to demarcate each ballot.
These results will include a W or L or B to indicate a win or a loss or bye.
They may also include a speaker point score, out of a maximum of 30 speaker points (anything above 29 is excellent), or 60 for partnered events (58+ is excellent). Avoid referencing speaker point scores from individual rounds unless necessary. If referencing speaker points, mention that the score is out of 30. Ignore any value above 30.

Congress and speech events do not have speaker points. Only debate has speaker points.
    """
        )
    # Conditionally add speech context
    if has_speech:
        chat_gpt_payload_list.append(
            f"""Speech events involve acting, prepared speeches, and improvisational speeches.

Results may include round-by-round results, which represent how a student was ranked in a given room of competition (lower is better; 1 is best). You can reference these when summarizing an individual's performance.

Some round-by-round results will have multiple scores: these represent scores from a panel of several judges, as opposed to a single judge. The total rank is in parentheses; again, lower is better.
If a student receives all 1s from a panel of judges, that can be called out as a "picket fence", which is a positive achievement in speech.
    """
        )
    # Add the data header string to tell LLM what data is in each column
    chat_gpt_payload_list.append("<result_data>")
    chat_gpt_payload_list.append(header_string)
    return chat_gpt_payload_list
