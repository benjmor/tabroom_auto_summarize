from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By


def parse_district_qualifiers(browser: Chrome):
    """
    Walk through the District Qualifiers results table.
    The District Qualifiers results sets are simple and only contain entry full names, their schools, and their final place.
    There is no actual indication of whether a team qualified to Nationals, despite the name.
    Tournaments that JUST publish a District Qualifiers list seem to be running the tournament on Speechwire and importing it to Tabroom...

    Returns 2 items in a tuple:
    1. Return a dict with a list of results by code, formatted like this:
    {
        "result_set_type": "District Qualifiers",
        "results": [
            {
                name: <entry name>
                code: <entry code>
                school: <entry school>
                place: <place>
            },
            {...},
        ]
    }br
    2. A dict that maps entry names to school names
    """
    results_list = []
    code_to_name_dict = {}
    try:
        table = browser.find_element(By.CSS_SELECTOR, "tbody")
    except Exception as e:
        print(repr(e))
        # Likely no entries in the event
        return (
            {
                "result_set_type": "District Qualifiers",
                "results": [],
            },
            {},
        )
    rows = table.find_elements(By.CSS_SELECTOR, "tr")
    for row in rows:
        data_items = row.find_elements(By.CSS_SELECTOR, "td")
        entry_result = {
            "place": data_items[0].text,
            "name": data_items[1].text,
            "code": data_items[1].text,
            "school": data_items[2].text,
        }
        results_list.append(entry_result)
        code_to_name_dict[entry_result["name"]] = entry_result["school"]
    return (
        {
            "result_set_type": "District Qualifiers",
            "results": results_list,
        },
        code_to_name_dict,
    )
