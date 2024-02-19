import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import Chrome
from selenium.common.exceptions import NoSuchElementException


def get_judge_map(
    tournament_id,
    browser: Chrome,
    school_short_name_dict: dict,
    unit_test=False,
):
    """
    Parses the "Judges" table and return a map of schools to judges

    Return structure:
    {
        "School Name": [
            "Judge 1",
            "Judge 2",
        ],
        "School Name 2": [
            "Judge 3",
            "Judge 4",
        ],
    }
    """
    judge_map = {}
    if unit_test:
        url = "file:///test_pages/judges_base.html"
    else:
        url = (
            f"https://www.tabroom.com/index/tourn/judges.mhtml?tourn_id={tournament_id}"
        )
    try:
        browser.get(url)
    except:
        logging.error(
            "Error when attempting to load Judges page, probably because the tournament does not publish it."
        )
        return judge_map
    judge_menu = browser.find_element(By.CLASS_NAME, "sidenote")
    judges_by_event = judge_menu.find_elements(By.CLASS_NAME, "odd")
    href_list = []
    for event in judges_by_event:
        href_list.append(
            event.find_element(By.TAG_NAME, "a").get_attribute("href")
        )  # Get the first href -- should be Link, not paradigms

    for href in href_list:
        browser.get(href)
        try:
            judge_table = browser.find_element(By.TAG_NAME, "tbody")
        except NoSuchElementException:
            logging.error(
                "Error when attempting to load a specific judge page, probably because the tournament does not have any judges in this category."
            )
            continue
        judge_rows = judge_table.find_elements(By.TAG_NAME, "tr")
        for row in judge_rows:
            row_data = row.find_elements(By.TAG_NAME, "td")
            judge_name = row_data[1].text + " " + row_data[2].text
            school_long_name = row_data[3].text
            school_short_name = school_short_name_dict.get(
                school_long_name, school_long_name
            )
            if school_short_name in judge_map:
                judge_map[school_short_name].append(judge_name)
            else:
                judge_map[school_short_name] = [judge_name]
    return judge_map


if __name__ == "__main__":
    tournament_id = "29810"
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_service = webdriver.ChromeService()
    browser = webdriver.Chrome(options=chrome_options, service=chrome_service)
    print(
        json.dumps(
            get_judge_map(
                tournament_id,
                browser=browser,
                unit_test=False,
            ),
            indent=4,
        )
    )
    chrome_service.stop()
