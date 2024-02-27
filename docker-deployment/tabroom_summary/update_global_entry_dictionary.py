import logging


def update_global_entry_dictionary(
    sections: list[dict], entry_dictionary: dict = {}, code_dictionary: dict = {}
):
    # Update entry dictionary by scraping an event's section data
    for section in sections:
        if "ballots" not in section:
            continue
        for ballot in section["ballots"]:
            entry_id = ballot["entry"]
            entry_name = ballot["entry_name"]
            entry_code = ballot["entry_code"]
            logging.debug(f"{entry_id}|{entry_name}")
            entry_dictionary[entry_id] = entry_name
            code_dictionary[entry_id] = entry_code
    return entry_dictionary, code_dictionary
