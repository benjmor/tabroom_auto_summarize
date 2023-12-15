import json


def group_data_by_school(results, all_schools: bool = False, school_name: str = ""):
    grouped_data = {}
    for result in results:
        if not all_schools and result["school_name"] != school_name:
            continue
        school_name = result["school_name"]
        if school_name not in grouped_data:
            grouped_data[school_name] = []
        grouped_data[school_name].append(result)
    return grouped_data


if __name__ == "__main__":
    results = [
        {"foo": "bar", "school_name": "aliceschool"},
        {"foo": "bad", "school_name": "bobschool"},
    ]

    print(
        json.dumps(
            group_data_by_school(results=results, all_schools=True),
            indent=4,
        )
    )
