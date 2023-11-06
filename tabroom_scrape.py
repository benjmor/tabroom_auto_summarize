import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs
import logging
import multiprocessing  # Adding multiprocessing to download several results concurrently
import selenium
from concurrent import futures

logging.basicConfig(level=logging.INFO)

# Enumerate some global things here
final_results_identifiers = [
    "Final Places"
]  # ["Prelim Seeds", "Speaker Awards", "Final Places"]
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
            logging.info(
                f"No table found for element ID {element_id}, trying without table number"
            )
            try:
                done = True  # Without a table number, we assume 1 table and break at the end
                element_id = result_id
                table = driver.find_element(By.ID, f"{element_id}")
            except selenium.common.exceptions.NoSuchElementException:
                logging.info(f"No table found for element ID {element_id}, either")
                break
        # Find the table headers
        csv_list = []
        headers = table.find_elements(By.CSS_SELECTOR, "thead th")
        if not headers:
            headers = table.find_elements(By.XPATH, "//th")
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
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        csv_list.append(header_names)
        for row in rows:
            # Skip header rows (rows that use this funky class name)
            # But also grab the column indices so we can check the school
            if row.get_attribute("class") == "yellowrow rotation odd":
                continue
            visible_results = [
                cell.text for cell in row.find_elements(By.CSS_SELECTOR, "td")
            ]
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
    event_name = option.get_attribute("innerHTML")
    link_map[event_name] = {}
    csv_map[event_name] = {}
    value = option.get_attribute("value")
    link = f"{base_url}&event_id={value}"
    logging.info(f"Link to results for {event_name}: {link}")
    driver = webdriver.Chrome(options=chrome_options)
    logging.info("Here!")
    driver.get(link)
    logging.info("Here2!")
    result_pages = driver.find_elements(By.CSS_SELECTOR, "div.sidenote a")
    for result in result_pages:
        try:
            result_name = result.text
        except Exception as ex:
            logging.error(repr(ex))
            continue
        if result_name in final_results_identifiers:
            result_url = result.get_attribute("href")
            result_id = parse_qs(urlparse(result_url).query)["result_id"][0]
            driver.get(result_url)
            link_map[event_name][result_name] = result_url
            result_csv = parse_results(driver, result_id, entry_to_school_name_dict)
            csv_map[event_name][result_name] = result_csv
            output.append(result_csv)
        if result_name in final_round_results_identifiers:
            result_url = result.get_attribute("href")
            round_id = parse_qs(urlparse(result_url).query)["round_id"][0]
            driver.get(result_url)
            link_map[event_name][result_name] = result_url
            result_csv = parse_results(driver, round_id, entry_to_school_name_dict)
            csv_map[event_name][result_name] = result_csv
            output.append(result_csv)
    return output


def main(tournament_id):
    global chrome_options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    # chrome_options.binary_location = CHROME_PATH

    # Start a new browser session
    browser = webdriver.Chrome(options=chrome_options)

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
    return results, entry_to_school_name_dict


if __name__ == "__main__":
    # This is not intended to be called as a main routine but is here for testing purposes.
    # Create an argument parser to take a tournament ID
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
