import json
import logging
import requests
import timeit

# TODO - review whether this is worth pursuing. It might save like 5-10% per call, but it feels more fragile to do it that way.


def scrape_entry_record(entry_record_url):
    """
    Returns a representation of an entry record.

    {
        full_entry_name: <full_entry_name>
        round_by_round_results: [
            {
                round_name: <round name>
                side: <aff / neg >
                opponent_code: <opp code>
                win_ballots: <#>
                loss_ballots:  <#>
            },
            ...
            {...}
        ]
    }
    """
    response = requests.get(entry_record_url)

    results_list = []
    # Get the entry name
    name_html_start_string = '<h4 class="nospace semibold">'
    entry_name_start = response.content.find(
        bytes(
            name_html_start_string,
            "utf-8",
        ),
    )
    entry_name_stop = response.content.find(
        b"</h4>\n\n\t\t\t\t\t<h6",
    )
    full_entry_name_raw = str(
        response.content[
            entry_name_start + len(name_html_start_string) : entry_name_stop
        ],
        "utf-8",
    )
    full_entry_name = (
        full_entry_name_raw.replace("\n", "").replace("\t", "").replace("&amp;", " & ")
    )

    return full_entry_name
    # Get the data from the table.
    rows = browser.find_elements(By.CLASS_NAME, "row")
    logging.info(f"Grabbing entry record results for {full_entry_name}")
    for row in rows:
        visible_results = [
            cell.text for cell in row.find_elements(By.CSS_SELECTOR, "span")
        ]
        entry_result = {}
        entry_result["round_name"] = visible_results[0]
        entry_result["side"] = visible_results[1]
        entry_result["opponent_code"] = visible_results[2].replace("vs ", "")
        entry_result["win_ballots"] = visible_results.count("W")
        entry_result["loss_ballots"] = visible_results.count("L")
        results_list.append(entry_result)

    entry_record = {
        "full_entry_name": full_entry_name,
        "round_by_round_results": results_list,
    }
    return entry_record


if __name__ == "__main__":
    # test_url = "https://www.tabroom.com/index/tourn/postings/entry_record.mhtml?tourn_id=24104&entry_id=4234996"
    test_url = "https://www.tabroom.com/index/tourn/postings/entry_record.mhtml?tourn_id=20134&entry_id=3555490"
    time_per_10_scrape = timeit.timeit(
        "scrape_entry_record(entry_record_url=test_url)",
        number=10,
        globals=globals(),
    )
    print(f"Each requests scrape takes {time_per_10_scrape/10} seconds.")
