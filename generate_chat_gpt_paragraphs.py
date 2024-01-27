import json
import logging
import openai
from generate_chat_gpt_prompt import generate_chat_gpt_prompt
from create_data_strings import create_data_strings
from generate_list_generation_prompt import generate_list_generation_prompt
from resolve_longname_to_shortname import resolve_longname_to_shortname


def generate_chat_gpt_paragraphs(
    tournament_data: dict,
    custom_url: str,
    school_count: int,
    state_count: int,
    has_speech: bool,
    has_debate: bool,
    entry_dictionary: dict,
    header_string: str,
    context: str,
    schools_to_write_up: list[str],
    grouped_data: dict,
    percentile_minimum: int,
    max_results_to_pass_to_gpt: int,
    read_only: bool,
    data_labels: list[str],
):
    for school in schools_to_write_up:
        logging.info(f"Starting results generation for {school}...")
        chat_gpt_payload = generate_chat_gpt_prompt(
            tournament_data=tournament_data,
            school_name=school,
            custom_url=custom_url,
            school_count=school_count,
            state_count=state_count,
            has_speech=has_speech,
            has_debate=has_debate,
            entry_dictionary=entry_dictionary,
            header_string=header_string,
            context=context,
        )
        try:
            school_filtered_tournament_results = grouped_data[school]
        except KeyError:
            # This is a super lazy way of handling school short names not matching long names.
            short_school_name = resolve_longname_to_shortname(school)
            school_filtered_tournament_results = grouped_data.get(short_school_name, [])
        if not school_filtered_tournament_results:
            logging.warning(f"No results found for {school}")
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
        chat_gpt_payload += create_data_strings(
            data_objects=top_sorted_filtered_school_results,
            data_labels=data_labels,
        )
        final_gpt_payload = "\r\n".join(chat_gpt_payload)
        openai.api_key_path = "openAiAuthKey.txt"
        logging.info(f"Generating summary for {school}")
        logging.info(f"GPT Prompt: {final_gpt_payload}")
        if read_only:
            logging.info(
                f"Skipping summary generation for {school} due to read-only mode"
            )
            continue
        else:
            body_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": final_gpt_payload},
                ],
            )["choices"][0]["message"]["content"]
            editor_payload = (
                "You are the editor of a local newspaper. Keep the tone factual and concise. Edit the following article improve its flow and grammar:\r\n"
                + body_response
            )
            editor_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": editor_payload},
                ],
            )["choices"][0]["message"]["content"]
            headline_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Generate a headline for this article. The response should be just a single headline, not in quotes",
                    },
                    {"role": "user", "content": editor_response},
                ],
            )["choices"][0]["message"]["content"]

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
            sorted_by_event_without_round_by_round.append(result_for_numbered_list)
        logging.info(f"Generating list of results for {school}")
        list_generation_prompt = generate_list_generation_prompt(headers=data_labels)
        numbered_list_prompt = (
            list_generation_prompt
            + "\r\n"
            + "\r\n".join(
                create_data_strings(
                    data_objects=sorted_by_event_without_round_by_round,
                    data_labels=data_labels,
                )
            )
        )

        # Provide Coach Information and Contact Information

        # Provide Judge Thank Yous

        logging.info(f"GPT Prompt: {numbered_list_prompt}")
        if read_only:
            logging.info(f"Skipping list generation for {school} due to read-only mode")
            continue
        else:
            numbered_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": numbered_list_prompt},
                ],
            )["choices"][0]["message"]["content"]

            with open(
                f"{tournament_data['name']}_summaries/{school}_summary.txt", "w"
            ) as f:
                f.write(
                    headline_response
                    + "\r\n"
                    + editor_response
                    + "\r\n"
                    + "Event-by-Event Results"
                    + "\r\n"
                    + numbered_response
                )
