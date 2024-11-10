# tabroom_auto_summarize

Generates AI-powered school-specific summaries of speech and debate competitions from Tabroom.com data.

# Website!

I now host a web version of this tool at [tabroomsummary.com](http://tabroomsummary.com). You can specify a tournament ID and a school name and it will return your summary (it may ask for a little bit of time to generate it first).

The website does have a small cost to me, so please USE the results you generate! Edit them and put them on social media, school newsletters, and local papers. Email them to principals, parents, and school board members! I'm fine with the costs as long as it's going to a good purpose.

# Disclaimer

This is still very much a work in progress -- Tabroom supports lots of different result types and I am gradually adding support for more of them.

I am not responsible for the contents generated by this script. If it says something mean, disheartening, or offensive, please...
1. **Edit the output** before you publish anything.
2. **Give feedback** about how to improve the software to avoid that issue in the future.

## Example Output

This is a sample output from Middleton High School's performance at the 2024 Wisconsin State Debate Tournament.

```
Middleton High School Stars Shine at Wisconsin State Debate Tournament

The Middleton High School Speech and Debate team delivered outstanding performances at the prestigious Wisconsin State Debate Tournament in West Bend, securing top-tier rankings. The powerful partnership of Nathan Kwon and Ben Pralat prevailed in the Varsity Public Forum (PF) rounds, maintaining a flawless victory record. Remarkably, they even accrued speaker points as high as 59 out of 60. Ben Pralat notched the top speaker position of the tournament, a significant accomplishment.

Alexa Garber and Shelley Yang also triumphed, securing second place with their series of victories and high speaker rating of 59 in the final round. Alexa Garber was a stand-out performer, earning the third position in the speaker awards for the Varsity PF category.

Vivian Liang deserves recognition for securing second place in the Speaker Awards, notable for high speaker points in Varsity PF. Andrew Wang also distinguished himself, nabbing second place in the Junior Varsity Public Forum Speaker Awards, testament to his commendable oratory skills.

Vivian Liang and Crystal Huang secured a respectable third place in Varsity PF Prelim Seeds with a perfect 60 speaker score. Additional notable achievements came from the teams of Noah Lucchesi and Brad Koeller, as well Ethan Sanders and Patrick DeCabooter, who placed fifth and sixth respectively in the Varsity PF Prelim Seeds. Crystal Huang, Nathan Kwon, Shelley Yang, Patrick DeCabooter, and Rishika Kommuri also earned recognition in the Speaker Awards line-up.

For information about how to participate, judge or volunteer in forensics, visit [here](https://wdca.org/). Keep the momentum going, Middleton!

Event-by-Event Results

1. **JV Public Forum**:
   - In Prelim Seeds, the team of Audrey Kim & Ananya Subramanian ranked 6th, Andrew Wang & Sai Kandukuri ranked 8th, Brady Nelson & Genesis Flores Lanzo ranked 12th, Akankshya Swain & Nathan Jerin ranked 15th, and Isabella Albiter & Zaima Haq ranked 16th.
   - In Speaker Awards, Andrew Wang came 2nd out of 32, Audrey Kim came 10th, Sai Kandukuri came 17th, Akankshya Swain was 22nd, Genesis Flores Lanzo came 25th, Ananya Subramanian was 26th, Brady Nelson secured 27th place, Isabella Albiter came 28th, Nathan Jerin was 29th, and Zaima Haq got 30th place.
   - In Final Places, the team of Audrey Kim & Ananya Subramanian secured 6th place, Andrew Wang & Sai Kandukuri came 8th, Brady Nelson & Genesis Flores Lanzo secured 12th place, Akankshya Swain & Nathan Jerin got 15th place, and Isabella Albiter & Zaima Haq secured 16th place.

2. **Varsity PF**:
   - In Prelim Seeds, the team of Nathan Kwon & Ben Pralat ranked 1st, Alexa Garber & Shelley Yang ranked 2nd, Vivian Liang & Crystal Huang ranked 3rd, Noah Lucchesi & Brad Koeller ranked 5th, Ethan Sanders & Patrick DeCabooter ranked 6th, Rishika Kommuri & Sieun (Michelle) Lee ranked 7th, Rhea Dalvie & Ria Karthik came 11th, Radhika Gupta & Sharmili Karthik ranked 23rd, and Ethan Yang & Tarun Chilakapati ranked 24th.
   - In Speaker Awards, Ben Pralat was 1st out of 48, Vivian Liang was 2nd, Alexa Garber and Nathan Kwon both tied for 3rd, Shelley Yang came 5th, Patrick DeCabooter came 6th, Crystal Huang came 7th, Rishika Kommuri was 10th, Ria Karthik was 11th, Brad Koeller came 15th, Rhea Dalvie secured 17th place, Noah Lucchesi secured 20th place, Ethan Sanders came 25th, Sieun (Michelle) Lee was 30th, Sharmili Karthik was 36th, Tarun Chilakapati was 38th, Radhika Gupta was 39th, and Ethan Yang was 46th.
```


# Documentation for nerds

This section is mostly for the nerds who want to help maintain the website

## GitHub Actions

The whole deployment process now runs via GitHub Actions. No need to run any of the `serverless deploy` commands locally.

## Website architecture

![image](https://github.com/benjmor/tabroom_auto_summarize/assets/44407400/b2d15de2-0b60-4687-935e-5700959d3588)

The website is powered by AWS serverless resources and Anthropic's Claude.

The main API/Lambda for handling requests uses the following logic:
1. If there is a `results.txt` file present for the given tournament and school, return `results.txt` and the underlying `gpt_prompt.txt` used to generate the results.
2. If there is a `gpt_prompt.txt` for the given tournament and school but no `results.txt`, send the `gpt_prompt.txt` file to Claude synchronously, wait for the response, then save the result to `results.txt` and display it to the user.
3. If there is no `gpt_prompt.txt` file present, kick off a process to generate `gpt_prompt.txt` files for all schools at the tournament. This is a long process, so let the user know that they should check back later.

Ideally, we never get to step 3. A batch process should look for recently-completed tournaments with results and generate prompts for them so that users don't need to spend a lot of time waiting for results.

## How TabroomSummary Scrapes Results

When a tournament is requested in TabroomSummary, its goal is to create a sorted list of results for ALL schools at the tournament.

This is the flow of functions within the `docker-deployment` folder, where the magic happens. This is what gets kicked off any time TabroomSummary gets a request for a tournament it hasn't seen before. This runs on an AWS Lambda.

- `main.handler()` # kick things off and eventually save the data
    - `tabroom_summary.main()`
        - `find_or_download_api_response()` # get data from the official API
        - `tabroom_scrape.main()` # scrape interesting data from the website, since the API is limited
          - `parse_results_wrapper()` -> `parse_results()` # Walk through each event result. Uses different logic for each different result page
            - `parse_final_places_results()` # Parses Final Results pages
            - `parse_prelim_records_results()` # Parses Prelim Records pages
            - `parse_dicts_from_prelim_seeds()` # Parses from Prelim Seeds pages
            - `parse_speaker_awards_results()` # Parses from Speaker Awards
            - `parse_district_qualifiers()` # Parses from NSDA District Qualifiers pages
          - `get_schools_and_states()` # Download metadata about the tournament's attendees
          - Compile a dictionary of what codes/names/schools each entry corresponds to, from the various `parse` functions' results
          - `resolve_longname_to_shortname()` # Tabroom uses two names for each school, a "long name" like "Bob Jones Academy" and a "short name" like "Bob Jones". This logic gets ridiculous for schools with names like "Academy High School."
          - `get_judge_map()` # Scrape the judges that worked for each school so we can thank them
          - `get_sweeps_results()` # Scrape any sweepstakes results
        - Walk through the API data and use it to update the codes/names/schools dictionary
        - `parse_result_sets()` # Parse results sets as given by the API response
          - `get_debate_results_from_rounds_only()` # If an event has no published results, scrape individual round results
          - `get_debate_or_congress_results()` # generate data based on the result set
          - `get_speech_results_from_final_places()` # generate data based on the result set
          - `get_speech_results_from_rounds_only()` # scrape individual round results if no formal results
        - `group_data_by_school()` # Take all the results and break them into groups based on school
        - `generate_llm_prompts()` # Walk through all schools and create LLM-ready prompts for each
    - Save the data to S3, where it can be consumed quickly to create articles

## Running TabroomSummary locally

### Prerequisites

Python 3.7+ installed.

### Installation and Usage

1. `cd docker-deployment` 
2. Install the required Python libraries: `pip install -r requirements.txt`
3. `python ./main.py --tournament-id <YOUR_TOURNAMENT_ID>` 

Results generation will take approximately 5 minutes for a typical local tournament. The output will be a folder of text files and a folder of webpages with a summary/summary webpage for each school.
