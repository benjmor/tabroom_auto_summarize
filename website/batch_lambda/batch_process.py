"""
Summary
This Lambda will look at the upcoming tournaments in the next week and save

The Lambda will then kick off a process (step function?) to look for results for existing tournaments

The output will eventually be GPT prompts for every tournament that completed since the last run.

This will NOT be backwards-looking -- it will only run on tournaments that start after 2024-03-17.
"""


