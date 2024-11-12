import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoSuchElementException


# TODO - currently, sweepstakes only pulls from the first listed sweepstakes page. Would need to figure out logic for handling multiple pages.
def parse_sweeps_page(
    browser,
    target_url,
):
    browser.get(target_url)
    try:
        # Find the table on the page
        table = browser.find_element(By.TAG_NAME, "table")
        # Find all rows in the table
        rows = table.find_elements(By.TAG_NAME, "tr")
    except NoSuchElementException:
        logging.warning(
            "No table found on the page. Probably not a valid sweepstakes result."
        )
        return []
    sweeps_list = []
    for row in rows:
        # Find all cells in the row
        cells = row.find_elements(By.TAG_NAME, "td")
        try:
            rank = cells[0].text
            school_name = cells[1].text
            points = cells[2].text
            row_data = {
                "rank": rank,
                "school_name": school_name,
                "points": points,
            }
            sweeps_list.append(row_data)
        except Exception as e:
            print(f"Error parsing row: {e}. Skipping.")
    return sweeps_list


def get_sweeps_results(browser):
    try:
        # Find the header labeled "Tournament-Wide"
        tournament_wide_section = browser.find_element(
            By.XPATH, "//div[h4[text()='Tournament-Wide']]"
        )

        # Get all links and titles within this section
        links = tournament_wide_section.find_elements(By.TAG_NAME, "a")

        logging.info("Sweepstakes Links:")
        for link in links:
            href = link.get_attribute("href")
            title = link.text
            logging.info(f"Title: {title}, URL: {href}")

        # For now, just grab the first link...
        url = links[0].get_attribute("href")
        sweeps_list = parse_sweeps_page(browser=browser, target_url=url)

    except Exception as e:
        logging.debug(f"No sweepstakes found.")
        return []

    return sweeps_list


if __name__ == "__main__":
    chrome_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    chrome_service = webdriver.ChromeService()
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging"]
    )  # attempting to suppress the USB read errors on Windows
    browser = webdriver.Chrome(options=chrome_options, service=chrome_service)
    # tournament_id = "28061" # Hockaday 2023
    tournament_id = "29595"  # CHSSA State 2024
    test_url = f"https://www.tabroom.com/index/tourn/results/index.mhtml?tourn_id={tournament_id}"
    browser.get(test_url)
    get_sweeps_results(tournament_id, browser, {})
