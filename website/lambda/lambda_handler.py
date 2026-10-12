import json
import boto3
import os
import logging
import re
import urllib.request
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError

"""
This is the main Lambda handler for the website.
"""


class Claude3Wrapper:
    """Encapsulates Claude 3 model invocations using the Amazon Bedrock Runtime client."""

    def __init__(self, client=None):
        """
        :param client: A low-level client representing Amazon Bedrock Runtime.
                       Describes the API operations for running inference using Bedrock models.
                       Default: None
        """
        self.client = client

    # snippet-start:[python.example_code.bedrock-runtime.InvokeAnthropicClaude3Text]
    def invoke_claude_3_with_text(self, prompt):
        """
        Invokes Anthropic Claude 3 Haiku to run an inference using the input
        provided in the request body.

        :param prompt: The prompt that you want Claude 3 to complete.
        :return: Inference response from the model.
        """

        # Initialize the Amazon Bedrock runtime client
        client = self.client or boto3.client(
            service_name="bedrock-runtime", region_name="us-east-1"
        )

        # Invoke Claude 3 with the text prompt
        account_id = boto3.client("sts").get_caller_identity().get("Account")
        model_id = f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/global.anthropic.claude-haiku-4-5-20251001-v1:0"

        try:
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(
                    {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 4 * 1024,
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"type": "text", "text": prompt}],
                            }
                        ],
                    }
                ),
            )

            # Process and print the response
            result = json.loads(response.get("body").read())
            input_tokens = result["usage"]["input_tokens"]
            output_tokens = result["usage"]["output_tokens"]
            output_list = result.get("content", [])

            logging.debug("Invocation details:")
            logging.debug(f"- The input length is {input_tokens} tokens.")
            logging.debug(f"- The output length is {output_tokens} tokens.")

            logging.debug(f"- The model returned {len(output_list)} response(s):")
            result_string = ""
            for output in output_list:
                logging.debug(output["text"])
                result_string = result_string + "\n" + output["text"]

            return result_string

        except ClientError as err:
            logging.error(
                "Couldn't invoke Claude 3 Haiku. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    # snippet-end:[python.example_code.bedrock-runtime.InvokeAnthropicClaude3Text]


def send_prompt_to_llm_and_save_to_s3(
    prompt,
    s3_client,
    bucket_name,
    key,
    numbered_list_prompt_path,
):
    """
    This function will take a prompt, pass it to Claude3, save it to S3, then
    """
    claude_client = Claude3Wrapper(
        boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
        )
    )
    full_response = claude_client.invoke_claude_3_with_text(
        prompt + "\n" + "Do not prepend paragraphs with labels like 'Paragraph 1'."
    )
    try:
        numbered_prompt = (
            s3_client.get_object(
                Bucket=bucket_name,
                Key=numbered_list_prompt_path,
            )["Body"]
            .read()
            .decode("utf-8")
        )
        bedrock_numbered_list_response = claude_client.invoke_claude_3_with_text(
            numbered_prompt
        )
        full_response = (
            full_response
            + "\n### Event-by-Event Results"
            + bedrock_numbered_list_response
        )
    except Exception as ex:
        print(f"Error getting numbered list prompt: {ex}")
        pass
    s3_client.put_object(
        Body=full_response,
        Bucket=bucket_name,
        Key=key,
    )
    return full_response


def lambda_handler(event, context):
    print(event)
    cors_headers = {
        "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
    }

    s3_client = boto3.client("s3")
    parsed_body = json.loads(event["body"])
    parsed_body["read_only"] = os.getenv("READ_ONLY", True)
    tournament_id = parsed_body["tournament"]
    school_name = str(parsed_body["school"]).strip()
    file_path_to_find_or_create = f"{tournament_id}/{school_name}/results.txt"
    raw_gpt_submission = f"{tournament_id}/{school_name}/gpt_prompt.txt"
    api_response_key = f"{tournament_id}/api_response.json"
    numbered_list_prompt_path = (
        f"{tournament_id}/{school_name}/numbered_list_prompt.txt"
    )
    bucket_name = os.getenv("DATA_BUCKET_NAME", "tabroom-summaries-data-bucket")
    numbered_list_prompt_content = None

    # Check if the requested results already exist -- return them if they do
    if len(school_name) > 0:  # explicitly skip empty names -- they are trouble.
        try:
            gpt_content = (
                s3_client.get_object(
                    Bucket=bucket_name,
                    Key=raw_gpt_submission,
                )["Body"]
                .read()
                .decode("utf-8")
            )
        except Exception:
            gpt_content = None
        try:
            numbered_list_prompt_content = (
                s3_client.get_object(
                    Bucket=bucket_name,
                    Key=numbered_list_prompt_path,
                )["Body"]
                .read()
                .decode("utf-8")
            )
        except Exception:
            numbered_list_prompt_content = None
        if gpt_content is not None:
            try:
                file_content = (
                    s3_client.get_object(
                        Bucket=bucket_name,
                        Key=file_path_to_find_or_create,
                    )["Body"]
                    .read()
                    .decode(encoding="utf-8", errors="replace")
                ).replace("\ufffd", "--")
            except Exception as ex:
                try:
                    file_content = send_prompt_to_llm_and_save_to_s3(
                        prompt=gpt_content,
                        s3_client=s3_client,
                        bucket_name=bucket_name,
                        key=file_path_to_find_or_create,
                        numbered_list_prompt_path=numbered_list_prompt_path,
                    )
                except Exception as ex:
                    logging.error(repr(ex))
                    file_content = "Prompt was not passed to the LLM; you can send the below prompt manually."
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(
                    {
                        "file_content": file_content
                        + "\n\nMore information about forensics (including how to compete, judge, or volunteer) can be found at [www.speechanddebate.org](www.speechanddebate.org), or by reaching out to the school's coach.",
                        "gpt_content": gpt_content,
                        "numbered_list_prompt_content": numbered_list_prompt_content,
                    }
                ),
            }

    # Check the tournament's end date to see if it is still ongoing. If it is, return a message indicating that the tournament is still ongoing.
    try:
        tournament_url = f"https://staging.tabroom.com/index/tourn/index.mhtml?tourn_id={tournament_id}"
        with urllib.request.urlopen(tournament_url) as response:
            page_content = response.read().decode("utf-8", errors="replace")
        # The tournament page is HTML, but some responses may be JSON or an empty body.
        # Guard against JSON parsing failures so we can still inspect the HTML.
        if page_content.lstrip().startswith("{"):
            data = json.loads(page_content)
        else:
            data = {"html": page_content}
    except Exception as ex:
        logging.error(f"Error occurred while fetching tournament details: {repr(ex)}")
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "file_content": "An error occurred while fetching tournament details.",
                    "gpt_content": "N/A",
                    "numbered_list_prompt_content": numbered_list_prompt_content,
                }
            ),
        }
    # In the HTML response, look for the end date in the format "Oct 10 to Oct 11 2026" in a class="smaller half"
    tournament_dates_match = re.search(
        r'<span class="smaller half">\s*\w{3}\s*\d{1,2}\s*to\s*(\w{3})\s*(\d{1,2})\s*(\d{4})',
        data.get("html", ""),
        re.DOTALL,
    )
    logging.warning(f"tournament_dates_match is {tournament_dates_match}")
    # extract the end date, which is everything after the "to" in the match
    if tournament_dates_match:
        tournament_dates = f"{tournament_dates_match.group(1)} {tournament_dates_match.group(2)} {tournament_dates_match.group(3)}"
        end_date = datetime.strptime(tournament_dates, "%b %d %Y").replace(
            tzinfo=timezone.utc
        )
        if datetime.now(tz=timezone.utc) - timedelta(hours=17) <= end_date:
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(
                    {
                        "file_content": f"The tournament is still ongoing and will end on {end_date.strftime('%B %d, %Y')}. Please check back after the tournament has concluded.",
                        "gpt_content": "N/A",
                        "numbered_list_prompt_content": numbered_list_prompt_content,
                    }
                ),
            }
    else:
        logging.error(
            f"Could not find tournament dates in the HTML for tournament {tournament_id}."
        )
        return {
            "isBase64Encoded": False,
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "file_content": f"Could not find tournament dates in the HTML for tournament {tournament_id}.",
                    "gpt_content": "N/A",
                    "numbered_list_prompt_content": numbered_list_prompt_content,
                }
            ),
        }
    # Also check if there is a "Results" tab in the id="tabnav" item
    # Example of HTML:
    # <ul id="tabnav">
    # 	<li class="selected">
    # 		 <a href="/index/tourn/index.mhtml?tourn_id=40386">Invite</a>
    # 	</li>
    #     <li class="">
    #             <a href="/index/tourn/judges.mhtml?tourn_id=40386">Results</a>
    #     </li>
    # </ul>

    results_tab_match = re.search(
        r"Results</a>",
        data.get("html", ""),
        re.IGNORECASE | re.DOTALL,
    )
    if not results_tab_match:
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "file_content": f"The tournament does not have a 'Results' tab, which indicates that results are not yet available. Please check back after the tournament has concluded.",
                    "gpt_content": "N/A",
                    "numbered_list_prompt_content": numbered_list_prompt_content,
                }
            ),
        }

    # Check if there are any files in the path bucket_name/tournament_id
    all_objects = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix=tournament_id,
    )
    # If there are no files at all, then skip this section and kick off a results generation
    if all_objects["KeyCount"] > 0:
        # See if a placeholder file exists -- used to prevent duplicate runs
        # placeholder.txt is a good proxy of whether a Lambda is [currently running or failed ungracefully] OR [never ran or completed successfully]
        try:
            placeholder_attributes = s3_client.get_object_attributes(
                Bucket=bucket_name,
                Key=f"{tournament_id}/placeholder.txt",
                ObjectAttributes=["ObjectSize"],
            )
        except Exception as ex:
            logging.warning(f"Error while looking up placeholder: {repr(ex)}")
            placeholder_attributes = None

        # Get a list of all the schools in the tournament so that the user knows what they can choose from
        # This logic just says "find all the subkeys within this tournament's key"
        # But make sure to exclude the `temp_results` folder
        school_set = set()
        for obj in all_objects["Contents"]:
            # Don't include files in the root of the tournament
            if len(obj["Key"].split("/")) > 2 and not re.search(
                r"temp_results", obj["Key"]
            ):
                school_set.add(obj["Key"].split("/")[1])

        # Get data to display the school list if there are schools present
        logging.warning(f"school_set is {school_set}")
        if len(school_set) > 0:
            school_data = "\n\n".join(sorted(list(school_set)))
        # Otherwise, display a message indicating the status
        else:
            # Placeholder is present but no school results ready -- have the user wait for results
            print(f"This is the placeholder_attributes: {placeholder_attributes}")
            if placeholder_attributes is not None and (
                (placeholder_attributes["LastModified"] + timedelta(hours=1))
                > datetime.now(tz=timezone.utc)
            ):
                school_data = "Still generating results! Check back soon!\nConsider opening a GitHub issue at https://github.com/benjmor/tabroom_auto_summarize/issues if this message persists."
            # no school results are present AND (the placeholder file is missing or outdated) -- data should be regenerated.
            else:
                school_data = "No schools found; will attempt to regenerate. Check back in about an hour."
                s3_client.put_object(
                    Body="Placeholder during generation.",
                    Bucket=bucket_name,
                    Key=f"{tournament_id}/placeholder.txt",
                )
                lambda_client = boto3.client("lambda")
                lambda_client.invoke(
                    FunctionName=os.environ["TABROOM_SUMMARY_LAMBDA_NAME"],
                    InvocationType="Event",
                    Payload=json.dumps(parsed_body),
                )
            return {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(
                    {
                        "file_content": school_data,
                        "gpt_content": "N/A",
                        "numbered_list_prompt_content": "N/A",
                    }
                ),
            }
        return {
            "isBase64Encoded": False,
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "file_content": (
                        "Tournament exists, but school does not. "
                        + "Check that your school name matches the official name in the Tabroom results. "
                        + f"Schools with results:\n\n{school_data}"
                    ),
                    "gpt_content": "N/A",
                    "numbered_list_prompt_content": numbered_list_prompt_content,
                }
            ),
        }

    # Put a placeholder file in the S3 bucket and then trigger the Lambda to generate the LLM prompts and results
    s3_client.put_object(
        Body="Placeholder during generation.",
        Bucket=bucket_name,
        Key=f"{tournament_id}/placeholder.txt",
    )
    lambda_client = boto3.client("lambda")
    lambda_client.invoke(
        FunctionName=os.environ["TABROOM_SUMMARY_LAMBDA_NAME"],
        InvocationType="Event",
        Payload=json.dumps(parsed_body),
    )
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps(
            {
                "file_content": "Results not yet generated, will attempt to generate them. Check back in about 15 minutes."
                + "\n\nNote: Huge tournaments (eg. Harvard) are not supported through this web interface. Create an Issue [here](https://github.com/benjmor/tabroom_auto_summarize/issues) if you want results from a specific large tournament.",
                "gpt_content": "N/A",
                "numbered_list_prompt_content": numbered_list_prompt_content,
            }
        ),
    }


if __name__ == "__main__":
    print(
        lambda_handler(
            {
                "body": json.dumps(
                    {
                        "tournament": "30430",
                        "school": "Lynbrook",
                        "read_only": "True",
                    }
                )
            },
            {},
        )
    )
