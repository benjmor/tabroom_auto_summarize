# Overview

This document outlines the design of the Tabroom Auto-Summarize website.

# Guiding principles

1. The website is intended to be self-service. A user should be able to request results from a completed tournament and receive them within 15 minutes
2. The website is privately hosted. There is no expectation of uptime or availability. The service is provided freely and open-source and can be copied at any time.

# General design

There is a single webpage hosted in S3 that has the following fields:

1. Auto-Summarize

A form that allows you to submit a tournament ID and school name and receive results from Tabroom.

If the results are present in S3 (bucketname/tournament_id/school_name.txt), return those.

If the results are not present in S3, kick off a process to generate the results and return a message to the user that their results are not available and that they should check back in about 10 minutes. The background process will upload them to S3.

The results will not have additional context.

2. Feedback form

Points to the GitHub Issue list.

# Backend

The website's front-end is a simple S3 website with a form that allows users to upload a tournament ID (5 digit number) and school name (string of up to 50 characters).

The form passes information to an API Gateway REST API (backed by AWS Lambda) that checks whether there is a file in S3 matching `mybucket/<tournament_ID>/<school_name>`. If the file is present, that file is returned. If not, the API gateway returns an error message.