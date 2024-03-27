import copy
from selenium.webdriver import Chrome
from .parse_results import parse_results


def parse_results_wrapper(
    thread_arguments: tuple = None,
    event_option=None,
    base_url=None,
    browser: Chrome = None,
    final_results_identifiers=None,
    final_round_results_identifiers=None,
    scrape_entry_records=None,
):
    """
    This is a helper function used to parse results either in parallel or serially.

    If thread_arguments is provided, it will parse results in parallel.
    If thread_arguments is not provided, it will parse results serially.
    """
    # Serial Case
    if thread_arguments is None:
        # Pack into a tuple and pass to the function
        my_tuple = (
            event_option,
            base_url,
            browser,
            final_results_identifiers,
            final_round_results_identifiers,
            scrape_entry_records,
        )
        return parse_results(my_tuple)

    # Parallel Case
    else:
        # Unpack the tuple
        (
            event_option,
            base_url,
            chrome_options_tuple,
            final_results_identifiers,
            final_round_results_identifiers,
            scrape_entry_records,
        ) = thread_arguments
        parallel_browser = Chrome(
            options=chrome_options_tuple[0],
            service=chrome_options_tuple[1],
        )
        # Update to use the new browser
        thread_arguments = (
            event_option,
            base_url,
            parallel_browser,
            final_results_identifiers,
            final_round_results_identifiers,
            scrape_entry_records,
        )
        result = parse_results(thread_arguments)
        parallel_browser.close()
        return result
