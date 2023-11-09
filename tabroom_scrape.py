import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse, parse_qs
import logging
import multiprocessing  # Adding multiprocessing to download several results concurrently
import selenium
from time import sleep
from concurrent import futures

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
)

# Enumerate some global things here
final_results_identifiers = [
    "Final Places",
    "Prelim Seeds",  # Sometimes need to parse the prelim seeds to scrape name/entry data
]  # ["Speaker Awards", "Final Places"]
final_round_results_identifiers = ["Finals Round results"]
entry_to_school_name_dict = {}
link_map = {}
csv_map = {}


def parse_results(driver, result_id, entry_to_school_dict):
    results_mega_list = []
    # Currently just Final Places
    table_num = 0
    done = False
    while not done:
        table_num = table_num + 1
        try:
            element_id = f"{result_id}-{table_num}"
            table = driver.find_element(By.ID, f"{result_id}-{table_num}")
        except selenium.common.exceptions.NoSuchElementException:
            logging.debug(
                f"No table found for element ID {element_id}, trying without table number"
            )
            try:
                done = True  # Without a table number, we assume 1 table and break at the end
                element_id = result_id
                table = driver.find_element(By.ID, f"{element_id}")
            except selenium.common.exceptions.NoSuchElementException:
                logging.debug(f"No table found for element ID {element_id}, either")
                break
            except StaleElementReferenceException:
                logging.error(
                    "Error within the results parser when reviewing secondary results table."
                )
        except StaleElementReferenceException:
            logging.error(
                "Error within the results parser when reviewing results table."
            )
        # Find the table headers
        csv_list = []
        try:
            headers = table.find_elements(By.CSS_SELECTOR, "thead th")
        except StaleElementReferenceException:
            logging.error(
                "Error within the results parser when finding results headers."
            )
        if not headers:
            try:
                headers = table.find_elements(By.XPATH, "//th")
            except StaleElementReferenceException:
                logging.error(
                    "Error within the results parser when finding results header using alternative approach."
                )
        header_names = [header.text for header in headers]
        # Get indices for school col and name col
        name_col = -1
        school_col = -1
        for index, header_name in enumerate(header_names, start=0):
            if header_name == "Institution":
                school_col = index
            elif header_name == "School":
                school_col = index
            if header_name == "Name":
                name_col = index
            elif header_name == "Entry":
                name_col = index
            if school_col > -1 and name_col > -1:
                break
        # The website has a hidden CSV of round results that are useful to feed to a ChatGPT.
        header_names.append("round_results_debate_only")
        try:
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        except StaleElementReferenceException:
            logging.error("Error within the results parser when grabbing results rows.")
        csv_list.append(header_names)
        for row in rows:
            # Skip header rows (rows that use this funky class name)
            # But also grab the column indices so we can check the school
            if row.get_attribute("class") == "yellowrow rotation odd":
                continue
            try:
                visible_results = [
                    cell.text for cell in row.find_elements(By.CSS_SELECTOR, "td")
                ]
            except StaleElementReferenceException:
                logging.error(
                    "Error within the results parser when getting cell text from body rows."
                )
            # Add that hidden CSV if it's there because we love it -- it contains round-by-round debate results
            try:
                visible_results.append(
                    row.find_element(By.XPATH, '//td[@class="hiddencsv"]')
                    .get_attribute("innerHTML")
                    .strip()
                )
            except selenium.common.exceptions.NoSuchElementException:
                logging.debug(
                    f"Could not add hidden results table for element ID {element_id}. This is normal for speech events, but weird for debate."
                )
            except StaleElementReferenceException:
                logging.error(
                    "Error within the results parser when finding hidden results."
                )
            csv_list.append(visible_results)
            entry_to_school_dict[visible_results[name_col]] = visible_results[
                school_col
            ]
        results_mega_list.append(csv_list)
        # TODO - remove junk like OpWPm, PtsPm-2HL, Z1Pm and RandPm
        # Potentially just take only two columns to the right of Wins?
    return results_mega_list


def parse_event_specific_results(option):
    """
    Function created to process all events in parallel
    """
    output = []
    try:
        event_name = option.get_attribute("innerHTML")
    except StaleElementReferenceException:
        logging.error("Error when attempting to load inner HTML.")
    link_map[event_name] = {}
    csv_map[event_name] = {}
    try:
        value = option.get_attribute("value")
    except StaleElementReferenceException:
        logging.error("Error when attempting to load value.")
    link = f"{base_url}&event_id={value}"
    logging.info(f"Link to results for {event_name}: {link}")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 5)
    try:
        driver.get(link)
    except WebDriverException:
        sleep_time = 5
        logging.error(
            f"Error when attempting to load {link}. Sleeping for {sleep_time} seconds before trying again."
        )
        sleep(secs=sleep_time)
        driver.get(link)
    driver.find_elements(By.CSS_SELECTOR, "div.sidenote a")
    result_pages = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.sidenote a"))
    )
    # Navigating through these results breaks them. Figure out a way to avoid that.
    result_page_details = []
    for result in result_pages:
        result_name = result.text
        identifiers_dict = {
            "result_id": final_results_identifiers,
            "round_id": final_round_results_identifiers,
        }
        for id in identifiers_dict.keys():
            if result_name in identifiers_dict[id]:
                result_url = result.get_attribute("href")
                result_id = parse_qs(urlparse(result_url).query)[id][0]
                link_map[event_name][result_name] = result_url
                result_page_details.append(
                    {
                        "result_id": result_id,
                        "result_url": result_url,
                        "result_name": result_name,
                    }
                )
    for result_page_detail in result_page_details:
        driver.get(result_page_detail["result_url"])
        result_csv = parse_results(
            driver, result_page_detail["result_id"], entry_to_school_name_dict
        )
        csv_map[event_name][result_page_detail["result_name"]] = result_csv
        output.append(result_csv)
    driver.quit()
    return output


def get_schools_and_states(tournament_id, chrome_options):
    """
    Parses the "Institutions in Attendance" table to get stats
    """
    school_set = set({})
    state_set = set({})
    url = f"https://www.tabroom.com/index/tourn/schools.mhtml?tourn_id={tournament_id}"
    browser = webdriver.Chrome(options=chrome_options)
    try:
        browser.get(url)
    except:
        logging.error(
            "Error when attempting to load Institutions in Attendance page, probably because the tournament does not publish it."
        )
        return school_set, state_set
    columns = browser.find_elements(By.CLASS_NAME, "third")
    for column in columns:
        schools = column.find_elements(By.CLASS_NAME, "fivesixth")
        for school in schools:
            school_set.add(school.text)
        states = column.find_elements(By.CLASS_NAME, "sixth")
        for state in states:
            state_set.add(state.text)
    return school_set, state_set


def main(tournament_id):
    global chrome_options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # attempting to suppress the USB read errors on Windows
    # chrome_options.add_argument("--disable-logging")
    # chrome_options.binary_location = CHROME_PATH

    # Start a new browser session
    browser = webdriver.Chrome(options=chrome_options)
    school_set, state_set = get_schools_and_states(tournament_id, chrome_options)

    # pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())

    # Navigate to the page with the dropdown menu
    global base_url
    base_url = f"https://www.tabroom.com/index/tourn/results/index.mhtml?tourn_id={tournament_id}"
    browser.get(base_url)

    # Find the dropdown menu element and get its options
    dropdown = browser.find_element(By.NAME, "event_id")
    # select = Select(WebDriverWait(browser, 2).until(EC.visibility_of_any_elements_located((By.NAME, "event_id"))))
    options = dropdown.find_elements(By.TAG_NAME, "option")

    # Loop through the options and scrape their child links
    with futures.ThreadPoolExecutor(10) as executor:
        results = list(executor.map(parse_event_specific_results, options))
    # pool.close()
    # pool.join()

    logging.info(link_map)

    # Close the browser session
    browser.quit()
    return {
        "results": results,
        "entry_to_school_dict": entry_to_school_name_dict,
        "school_set": school_set,
        "state_set": state_set,
    }


if __name__ == "__main__":
    # This is not intended to be called as a main routine but is here for testing purposes.
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t",
        "--tournament-id",
        help="Tournament ID (typically a 5-digit number) of the tournament you want to generate results for.",
        required=True,
    )
    args = parser.parse_args()
    tournament_id = args.tournament_id
    results = main(tournament_id=tournament_id)
    print(results)
