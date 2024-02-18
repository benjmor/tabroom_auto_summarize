from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import logging


def scrape_entry_record(browser, entry_record_url):
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
    browser.get(entry_record_url)
    results_list = []
    full_entry_name = (
        browser.find_element(By.CLASS_NAME, "main")
        .find_element(By.CSS_SELECTOR, "h4")
        .text
    )
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
    test_url = "https://www.tabroom.com/index/tourn/postings/entry_record.mhtml?tourn_id=24104&entry_id=4234996"
    # Start a new browser session
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # attempting to suppress the USB read errors on Windows
    # chrome_options.add_argument("--disable-logging")
    # chrome_options.binary_location = CHROME_PATH
    browser = webdriver.Chrome(options=chrome_options)
    browser.get(test_url)
    print(
        json.dumps(
            scrape_entry_record(driver=browser, entry_record_url=test_url),
            indent=4,
        )
    )
    browser.quit()
