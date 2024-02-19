import boto3
import json
import logging
import os
from openai import OpenAI
from .generate_chat_gpt_prompt import generate_chat_gpt_prompt
from .create_data_strings import create_data_strings
from .generate_list_generation_prompt import generate_list_generation_prompt


def generate_chat_gpt_paragraphs(
    tournament_data: dict,
    custom_url: str,
    school_count: int,
    state_count: int,
    has_speech: bool,
    has_debate: bool,
    entry_dictionary: dict,
    context: str,
    schools_to_write_up: list[str],
    grouped_data: dict,
    percentile_minimum: int,
    max_results_to_pass_to_gpt: int,
    read_only: bool,
    data_labels: list[str],
    judge_map: dict,
    school_short_name_dict: dict,
    open_ai_key_path: str = None,
    open_ai_key_secret_name: str = None,
    debug: bool = False,
):
    all_schools_dict = {}
    # Read the OpenAI API key from a file or AWS Secrets Manager
    if open_ai_key_path:
        with open(open_ai_key_path, "r") as f:
            api_key = f.read()
    else:
        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
        api_key = secrets_client.get_secret_value(SecretId=open_ai_key_secret_name)[
            "SecretString"
        ]
    client = OpenAI(api_key=api_key)
    for school_long_name in schools_to_write_up:
        short_school_name = school_short_name_dict[school_long_name]
        school_filtered_tournament_results = grouped_data.get(short_school_name, [])
        all_schools_dict[short_school_name] = {}
        logging.info(f"Starting results generation for {short_school_name}...")
        if not school_filtered_tournament_results:
            logging.warning(f"No results found for {short_school_name}")
            continue
        sorted_school_results = sorted(
            school_filtered_tournament_results,
            key=lambda x: float(x["percentile"]),
            reverse=True,
        )
        # If there is at least one result above the percentile minimum, filter out any results below the percentile minimum
        if int(float(sorted_school_results[0]["percentile"])) > percentile_minimum:
            logging.info(
                "Found a result above the percentile minimum, filtering out results below threshold"
            )
            threshold_school_results = filter(
                lambda x: float(x["percentile"]) > percentile_minimum,
                sorted_school_results,
            )
            sorted_filtered_school_results = list(threshold_school_results)
        else:
            sorted_filtered_school_results = sorted_school_results

        # Filter down to just the top 15 results (based on percentile) to get better results for large schools
        if len(sorted_filtered_school_results) > max_results_to_pass_to_gpt:
            top_sorted_filtered_school_results = sorted_filtered_school_results[
                0 : max_results_to_pass_to_gpt - 1
            ]
        else:
            top_sorted_filtered_school_results = sorted_filtered_school_results
        logging.info(
            f"School specific results without any filtering:\r\n{json.dumps(sorted_school_results, indent=4)}"
        )
        data_labels_without_percentile = [
            label for label in data_labels if label != "percentile"
        ]
        data_strings = create_data_strings(
            data_objects=top_sorted_filtered_school_results,
            data_labels=data_labels_without_percentile,
        )
        chat_gpt_payload = generate_chat_gpt_prompt(
            tournament_data=tournament_data,
            school_name=school_long_name,
            school_count=school_count,
            state_count=state_count,
            has_speech=has_speech,
            has_debate=has_debate,
            entry_dictionary=entry_dictionary,
            header_string="|".join(data_labels_without_percentile),
            context=context,
            data_strings=data_strings,
        )
        chat_gpt_payload += data_strings
        final_gpt_payload = "\n".join(chat_gpt_payload)
        all_schools_dict[short_school_name]["gpt_prompt"] = final_gpt_payload

        logging.info(f"Generating summary for {short_school_name}")
        logging.info(f"GPT Prompt: {final_gpt_payload}")
        if read_only:
            logging.info(
                f"Skipping summary generation for {short_school_name} due to read-only mode"
            )
            continue
        else:
            body_response = (
                client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are concise, professional newspaper editor.",
                        },
                        {"role": "user", "content": final_gpt_payload},
                    ],
                )
                .choices[0]
                .message.content
            )
            if judge_map.get(short_school_name, []):
                judge_string = (
                    f"\r\nThis tournament was made possible with the help of the following judges from {short_school_name}: "
                    + ", ".join(judge_map.get(short_school_name, []))
                )
            else:
                judge_string = ""
            body_response = (
                body_response
                + "\r\n"
                + "More information about forensics (including how to compete, judge, or volunteer) can be found at www.speechanddebate.org, or by reaching out to the school's coach."
                + judge_string
            )

            all_schools_dict[short_school_name]["unedited_response"] = body_response
            # editor_payload = (
            #     "You are the editor of a local newspaper. Keep the tone factual and concise. Edit the following article improve its flow and grammar:\r\n"
            #     + body_response
            # )
            # editor_response = (
            #     client.chat.completions.create(
            #         model="gpt-4",
            #         messages=[
            #             {"role": "system", "content": "You are a helpful assistant."},
            #             {"role": "user", "content": editor_payload},
            #         ],
            #     )
            #     .choices[0]
            #     .message.content
            # )
            # all_schools_dict[school]["edited_response"] = editor_response
            # headline_response = (
            #     client.chat.completions.create(
            #         model="gpt-4",
            #         messages=[
            #             {
            #                 "role": "system",
            #                 "content": "Generate a headline for this article. The response should be just a single headline, not in quotes",
            #             },
            #             {"role": "user", "content": editor_response},
            #         ],
            #     )
            #     .choices[0]
            #     .message.content
            # )
            # all_schools_dict[school]["headline_response"] = headline_response

        sorted_by_event = sorted(
            school_filtered_tournament_results,
            key=lambda x: x["event_name"],
            reverse=False,
        )
        sorted_by_event_without_round_by_round = []
        # Reduce to just the essentials
        for result_for_numbered_list in sorted_by_event:
            # Remove round-by-round results from the numbered list -- not required
            result_for_numbered_list.pop("results_by_round")
            if float(result_for_numbered_list["percentile"]) < percentile_minimum:
                continue
            sorted_by_event_without_round_by_round.append(result_for_numbered_list)
        if len(sorted_by_event_without_round_by_round) == 0:
            logging.warning(
                f"No results found for {short_school_name} above the percentile minimum, returning just the summary paragraph."
            )
            full_response = (
                # headline_response
                # + "\r\n"
                # + editor_response
                body_response
            )
        else:
            logging.info(f"Generating list of results for {short_school_name}")
            list_generation_prompt = generate_list_generation_prompt(
                headers=data_labels
            )
            numbered_list_prompt = (
                list_generation_prompt
                + "\r\n"
                + "\r\n".join(
                    create_data_strings(
                        data_objects=sorted_by_event_without_round_by_round,
                        data_labels=data_labels_without_percentile,
                    )
                )
            )
            all_schools_dict[short_school_name][
                "numbered_list_prompt"
            ] = numbered_list_prompt

            logging.info(f"GPT Prompt: {numbered_list_prompt}")
            if read_only:
                logging.info(
                    f"Skipping list generation for {short_school_name} due to read-only mode"
                )
                continue
            else:
                numbered_response = (
                    client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful assistant.",
                            },
                            {"role": "user", "content": numbered_list_prompt},
                        ],
                    )
                    .choices[0]
                    .message.content
                )

            full_response = (
                # headline_response
                # + "\r\n"
                # + editor_response
                body_response
                + "\r\n"
                + "Event-by-Event Results"
                + "\r\n"
                + numbered_response
            )
        all_schools_dict[short_school_name]["full_response"] = full_response
    return all_schools_dict
