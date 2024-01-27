from datetime import datetime


def generate_chat_gpt_prompt(
    tournament_data,
    school_name,
    school_count,
    entry_dictionary,
    header_string,
    custom_url=None,
    state_count=1,
    has_speech=False,
    has_debate=False,
    context="",
):
    """
    Generates a text prompt to send to ChatGPT, telling it what to create. Does not contain the results, but does contain a header.

    Just add results data and this baby is ready to send to ChatGPT.

    Returns a list of strings with ChatGPT prompt pieces.
    """
    start_date = datetime.strptime(
        tournament_data["start"].split(" ")[0], "%Y-%m-%d"
    ).strftime(
        "%B %d, %Y",
    )  # The start time is useless and inaccurate, just use the date
    if custom_url:
        follow_up_url = custom_url
    else:
        follow_up_url = "https://www.speechanddebate.org"
    if state_count > 1:
        state_detail = f" from {state_count} states."
    else:
        state_detail = "."
    chat_gpt_basic_prompt = f"""
    The following data represents results of a team's performance at a speech and debate tournament called {tournament_data["name"]} held in {tournament_data["city"]} ({tournament_data["state"]}) on {start_date}. {context}
    
    The tournament was attended by {len(entry_dictionary)} student entries and {school_count} schools{state_detail}

    Write a 3 paragraph summary for the {school_name} speech and debate team social media feed. Use as many student names of {school_name} students as reasonable. Write concisely and professionally.
    At the end, indicate that general information about forensics (including how to compete, judge, or volunteer) can be found at {follow_up_url}.
    
    Include individuals' rankings and statistics, such as number of wins. When referencing results, you should include the total number of entries in the event. Don't include raw percentile information in the output.

    Do not use the definite article 'the' before the names of events.
    """
    # Removed: Wins should be listed earlier than other achievements. Varsity results should be listed before Novice or Junior Varsity (JV) results.
    chat_gpt_debate_prompt = f"""
    Final Places and Speaker Awards are more important than Prelim seeds.

    Terms like 'Doubles', 'Octos', and 'Quarters' may be used to indicate the elimination round a team reached.
    Doubles refers to the Round of 32 (also known as double-octofinals), Octos refers to the Round of 16 (octofinals), and Quarters refers to the Round of 8 (quarterfinals), respectively.
    Use these terms to describe the elimination round a debater reached.

    PF is an abbreviation for Public Forum, a 2-on-2 style of debate.
    LD is an abbreviation for Lincoln-Douglas, a 1-on-1 style of debate.
    CX is an abbreviation for Cross-examination (aka Policy), a 2-on-2 style of debate.
    These abbreviations may be prefixed with V, JV, or N, indicating Varsity, Junior Varsity, or Novice level.

    Winning a first place speaker award should be referred to as winning top speaker for the tournament.

    Team entries might be indicated with just last names. If so, those teams should be referred to as "the team of", followed by the last names.

    Results may include round-by-round results, delimited by a "|" or "!" character or &nbsp string to demarcate each round, which represent how a student performed in a single round.
    Single round results will include a W or L or B to indicate a win or a loss or bye.
    They may also include a speaker point score, out of a maximum of 30 speaker points (anything above 29 is excellent). If referencing speaker points, mention that the score is out of 30.
    You may see summed speaker points, representing scores added between teammates. These combined speaker points are instead out of a maximum of 60.
    You can reference these single round results when summarizing an individual's performance.

    Avoid referencing speaker point scores from individual rounds unless necessary.
    """
    chat_gpt_speech_prompt = f"""
    Speech events involve acting, prepared speeches, and improvisational speeches.

    Results may include round-by-round results, which represent how a student was ranked in a given room of competition (1 is best). You can reference these when summarizing an individual's performance.

    Some round-by-round results will have multiple scores: these represent scores from a panel of several judges, as opposed to a single judge.
    If a student receives all 1s from a panel of judges, that can be called out as a "picket fence", which is a positive achievement in speech.
    """

    chat_gpt_payload = [chat_gpt_basic_prompt]
    if has_debate:
        chat_gpt_payload.append(chat_gpt_debate_prompt)
    if has_speech:
        chat_gpt_payload.append(chat_gpt_speech_prompt)
    chat_gpt_payload.append(header_string)
    return chat_gpt_payload
