import logging
from selenium import webdriver
from selenium.webdriver.common.by import By


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
