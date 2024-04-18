import argparse


def parse_arguments():
    # PARSE INPUT FROM USER
    parser = argparse.ArgumentParser(
        prog="tabroom_summary",
        description="Uses an LLM to create summaries of Tabroom results",
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
        help="Read-only mode. Will pull data from Tabroom and format it but will not send the payload to the LLM.",
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
        help="Maximum number of results to pass to the LLM. If this number is exceeded, the results will be truncated.",
        type=int,
        default=15,
    )
    parser.add_argument(
        "-c",
        "--context",
        help="An additional phrase of context to add about the tournament. YEAH THERE'S PROMPT INJECTION RISK HERE, BUT YOU'RE RUNNING THIS ON YOUR OWN INFRASTRUCTURE.",
        required=False,
        default="",
    )
    parser.add_argument(
        "--scrape-entry-records-bool",
        help="If true, scrape the entry records from Tabroom.com. If false, will only use the data from the Tabroom API.",
        action="store_true",
        required=False,
    )
    key_source = parser.add_mutually_exclusive_group(required=True)
    key_source.add_argument(
        "--open-ai-key-path",
        help="If provided, will read the OpenAI API key from this local file instead of AWS Secrets Manager.",
        required=False,
    )
    key_source.add_argument(
        "--open-ai-key-secret-name",
        help="If provided, will read the OpenAI API key from AWS Secrets Manager using this secret name.",
        required=False,
    )
    return parser.parse_args()
