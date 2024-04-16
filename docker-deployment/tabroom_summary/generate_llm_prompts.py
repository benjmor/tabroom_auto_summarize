import boto3
import json
import logging
import os
from .generate_llm_prompt_header import generate_llm_prompt_header
from .create_data_strings import create_data_strings
from .generate_list_generation_prompt import generate_list_generation_prompt


def generate_llm_prompts(
    tournament_data: dict,
    # custom_url: str,
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
    data_labels: list[str],
    judge_map: dict,
    school_short_name_dict: dict,
    default_qualifier_count: int,
    remove_duplicate_prelim_final_places_rows: bool = True,
):
    all_schools_dict = {}
    tournament_id = tournament_data["id"]
    for school_long_name in schools_to_write_up:
        short_school_name = school_short_name_dict[school_long_name]
        # If there is already a results.txt file for the school, continue early
        if os.path.exists(f"{tournament_id}/{short_school_name}/results.txt"):
            logging.debug(f"Skipping {short_school_name} due to existing results")
            continue
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
        # Remove Prelim Seeds if there is a Final Places entry with the same data
        # This is O(N^2) but shouldn't be a huge issue except for MASSIVE school entries (100+)
        if remove_duplicate_prelim_final_places_rows:
            for outer_result in sorted_school_results:
                if outer_result["result_set"] == "Final Places":
                    target_result_set = "Prelim Seeds"
                    current_entry = outer_result["entry_name"]
                    current_rank = outer_result["rank"]
                    for inner_result in sorted_school_results:
                        if (
                            inner_result["result_set"] == target_result_set
                            and inner_result["entry_name"] == current_entry
                            and inner_result["rank"] == current_rank
                        ):
                            sorted_school_results.remove(inner_result)
                            break

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
        logging.debug(
            f"School specific results without any filtering:\r\n{json.dumps(sorted_school_results, indent=4)}"
        )
        data_labels_without_percentile = [
            label for label in data_labels if label != "percentile"
        ]
        data_strings = create_data_strings(
            data_objects=top_sorted_filtered_school_results,
            data_labels=data_labels_without_percentile,
        )
        llm_payload = generate_llm_prompt_header(
            tournament_data=tournament_data,
            school_name=school_long_name,
            short_school_name=short_school_name,
            school_count=school_count,
            state_count=state_count,
            has_speech=has_speech,
            has_debate=has_debate,
            entry_dictionary=entry_dictionary,
            header_string="|".join(data_labels_without_percentile),
            context=context,
            data_strings=data_strings,
            judge_map=judge_map,
            default_qualifier_count=default_qualifier_count,
        )
        llm_payload += data_strings
        llm_payload.append("</result_data>")
        final_llm_payload = "\n".join(llm_payload)
        all_schools_dict[short_school_name]["gpt_prompt"] = final_llm_payload

        logging.debug(f"LLM Prompt: {final_llm_payload}")

        ###  Generate numbered list prompt
        sorted_by_event = sorted(
            sorted_school_results,
            key=lambda x: x["event_name"],
            reverse=False,
        )
        sorted_by_event_without_round_by_round = []

        # Reduce to just the essentials
        for result_for_numbered_list in sorted_by_event:
            # Remove round-by-round results from the numbered list -- not required
            try:
                result_for_numbered_list.pop("results_by_round")
            except KeyError:
                pass  # already not present
            if float(result_for_numbered_list["percentile"]) < percentile_minimum:
                continue
            sorted_by_event_without_round_by_round.append(result_for_numbered_list)
        if len(sorted_by_event_without_round_by_round) == 0:
            numbered_list_prompt = ""
        else:
            logging.info(f"Generating list of results for {short_school_name}")
            list_generation_prompt = generate_list_generation_prompt(
                headers=data_labels
            )
            numbered_list_prompt = (
                list_generation_prompt
                + "\n"
                + "\n\n".join(
                    create_data_strings(
                        data_objects=sorted_by_event_without_round_by_round,
                        data_labels=data_labels_without_percentile,
                    )
                )
                + "\n"
                + "</result_data>"
            )
            all_schools_dict[short_school_name][
                "numbered_list_prompt"
            ] = numbered_list_prompt

        # If running outside of Lambda, save off results at the end
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is None:
            os.makedirs(
                f"{tournament_id}/{short_school_name}",
                exist_ok=True,
            )
            with open(f"{tournament_id}/{short_school_name}/gpt_prompt.txt", "w") as f:
                f.write(final_llm_payload)
            with open(
                f"{tournament_id}/{short_school_name}/numbered_list_prompt.txt", "w"
            ) as f:
                f.write(numbered_list_prompt)
    return all_schools_dict
