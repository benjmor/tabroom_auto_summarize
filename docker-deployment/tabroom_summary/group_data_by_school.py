import json


def group_data_by_school(
    results,
    school_short_name_dict: dict,
):
    """
    Given a list of results and a dictionary that maps long school names to short school names
    Group the results by the school's short name.
    Returns a dict keyed by short school name, containing a list of results for that school
    """
    grouped_data = {}
    for result in results:
        school_long_name = result["school_name"]
        try:
            school_short_name = school_short_name_dict[school_long_name]
        except KeyError:
            # Assume the long name is the short name if it's not in the dict
            school_short_name = school_long_name
        if school_short_name not in grouped_data:
            grouped_data[school_short_name] = []
        grouped_data[school_short_name].append(result)
    return grouped_data


if __name__ == "__main__":
    results = [
        {"foo": "bar", "school_name": "aliceschool"},
        {"foo": "bad", "school_name": "bobschool"},
    ]
    school_short_name_dict = {
        "aliceschool": "alice",
        "bobschool": "bob",
    }

    print(
        json.dumps(
            group_data_by_school(
                results=results,
                school_short_name_dict=school_short_name_dict,
                all_schools=True,
            ),
            indent=4,
        )
    )
