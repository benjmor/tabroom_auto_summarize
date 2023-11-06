# tabroom_auto_summarize

Generates AI-powered school-specific summaries of speech and debate competitions from Tabroom.com data

# Disclaimer

This is still very much a work in progress -- Tabroom supports lots of different result types and I am gradually adding support for more of them.

I am not responsible for the contents generated by this script. If it says something mean, disheartening, or offensive, please 1. edit it before you publish anything, and 2. give feedback about how to improve the software to avoid that issue in the future.

This project is not directly affiliated with the NSDA, which you probably could infer from the web scraping it's doing instead of using actual APIs.

I wish this project were affiliated with NSDA, so if you've got any ins with them, hit me up!

# Prerequisites

Python 3.7+ installed.

# Installation

1. Install the required Python libraries: `pip install -r requirements.txt`
2. Create an [OpenAI key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key) and save the key to `openAiAuthKey.txt` in the same folder as the script. Remember never to upload this key anywhere! Treat it like a password.

# Example Usage (single school)

First, find the tournament ID from the Tabroom URL of the tournament you are interested in (these examples use `11111`).

To run for all schools at the tournament:

```bash
python tabroom_summary --tournament-id 11111 --all-schools
```

To run for a single school at the tournament:

```bash
python tabroom_summary --tournament-id 11111 --school-name "The Milford School for Children"

```

It will take approximately 5 minutes for a typical local tournament. The output will be a folder of text files and a folder of webpages with a summary/summary webpage for each school.

After generating the content, feel free to edit it as needed and post it to social media. And tell your friends if you like the project!
