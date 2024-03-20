def generate_list_generation_prompt(headers: list[str]):
    return f"""
Create a numbered list of the following speech and debate tournament event results, so that each event is a new number in the list, and each event contains results from all students in that event.
Do not include the school name in the individual results entry.
Team entries might be indicated with just last names, and will typically not contain first names. Those teams should be referred to as "the team of", followed by the last names.

PF is an abbreviation for Public Forum, a 2-on-2 style of debate.
LD is an abbreviation for Lincoln-Douglas, a 1-on-1 style of debate.
CX is an abbreviation for Cross-examination (aka Policy), a 2-on-2 style of debate.
These abbreviations may be prefixed with V, JV, or N, indicating Varsity, Junior Varsity, or Novice level.

Don't create separate line-items for different types of results. For example, PF Speaker Awards and PF Final Places should both appear on the same numbered line.

Expand certain values to make them more readable: if a rank is given as 3/17, write it as '3rd place out of 17'. If a win-loss record is 3W1L, refer to it as '3 wins and 1 loss' or 'a record of 3-1'.

Bold the name of the event by putting 2 asterisks around it.
For example:
1. **Event Name**: StudentName (3rd place) made finals and StudentName6 placed 5th. StudentName6 was also 5th speaker.
2. **Event Name2**: StudentName2 won 1st place and StudentName5 took 3rd place. StudentName3 (8th place) and StudentName4 (10th place) made semifinals.

ONLY INCLUDE RESULTS FROM THE RESULTS DATA. DO NOT INCLUDE ANY RESULTS THAT DO NOT APPEAR IN RESULT_DATA.

<result_data>
{"|".join(headers)}
</result_data>
    """


if __name__ == "__main__":
    print(generate_list_generation_prompt())
