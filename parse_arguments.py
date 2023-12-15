import argparse


def parse_arguments():
    # PARSE INPUT FROM USER
    parser = argparse.ArgumentParser(
        prog="tabroom_summary",
        description="Uses ChatGPT to create summaries of Tabroom results",
    )
    school_args = parser.add_mutually_exclusive_group(required=True)
    school_args.add_argument(
        "-s",
        "--school-name",
        help="Name of the school that your article will focus on.",
        required=False,
    )
    school_args.add_argument(
        "--all-schools",
        action="store_true",
        help="Generate summaries for all schools in the Tabroom data.",
    )
    parser.add_argument(
        "-t",
        "--tournament-id",
        help="Tournament ID (typically a 5-digit number) of the tournament you want to generate results for.",
        required=True,
    )
    parser.add_argument(
        "-u",
        "--custom-url",
        help="Custom URL of the tournament you want to generate results for. For example, a league website.",
        required=False,
    )
    parser.add_argument(
        "-r",
        "--read-only",
        help="Read-only mode. Will pull data from Tabroom and format it but will not send the payload to ChatGPT.",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-p",
        "--percentile-minimum",
        help="Minimum percentile for entries to be included in the summary.",
        type=int,
        default=50,
    )
    parser.add_argument(
        "-m",
        "--max-results",
        help="Maximum number of results to pass to ChatGPT. If this number is exceeded, the results will be truncated.",
        type=int,
        default=15,
    )
    return parser.parse_args()
