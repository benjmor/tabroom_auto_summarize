data "aws_caller_identity" "current" {}
data "aws_region" "current" {}


data "archive_file" "schedule_scrape_lambda_source" {
  type        = "zip"
  source_file = "${path.module}/batch_scrape_lambda/batch_scrape_lambda.py"
  output_path = "${path.module}/batch_scrape_lambda/batch_scrape_lambda.zip"
}

data "aws_iam_policy_document" "schedule_scrape_lambda_permissions" {
  statement {
    actions = [
      "sns:Publish",
    ]
    resources = [
      "*",
    ]
  }

  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [
      "arn:aws:dynamodb:us-east-1:238589881750:table/tabroom_tournaments",
      "arn:aws:dynamodb:us-east-1:238589881750:table/tabroom_tournaments/*",
    ]
  }
}


data "archive_file" "batch_process_lambda_source" {
  type        = "zip"
  source_file = "${path.module}/batch_process_lambda/batch_process_lambda.py"
  output_path = "${path.module}/batch_process_lambda/batch_process_lambda.zip"
}

data "aws_iam_policy_document" "batch_process_lambda_permissions" {
  statement {
    actions = [
      "sns:Publish",
    ]
    resources = [
      "*",
    ]
  }

  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      "arn:aws:lambda:us-east-1:238589881750:function:docker-selenium-lambda-tabroom-prod-main",
      "arn:aws:lambda:us-east-1:238589881750:function:docker-selenium-lambda-tabroom-prod-main:*"
    ]
  }

  statement {
    actions = [
      # "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [
      "arn:aws:dynamodb:us-east-1:238589881750:table/tabroom_tournaments",
      "arn:aws:dynamodb:us-east-1:238589881750:table/tabroom_tournaments/*",
    ]
  }
}


# TEST
data "archive_file" "recent_summaries_lambda_source" {
  type        = "zip"
  source_file = "${path.module}/recent_summaries_lambda/recent_summaries_lambda.py"
  output_path = "${path.module}/recent_summaries_lambda/recent_summaries_lambda.zip"
}

data "aws_iam_policy_document" "recent_summaries_lambda_permissions" {
  statement {
    actions = [
      "sns:Publish",
    ]
    resources = [
      "*",
    ]
  }

  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "arn:aws:s3:::tabroomsummary.com/recent_tournaments.txt",
    ]
  }

  statement {
    actions = [
      # "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [
      "arn:aws:dynamodb:us-east-1:238589881750:table/tabroom_tournaments",
      "arn:aws:dynamodb:us-east-1:238589881750:table/tabroom_tournaments/*",
    ]
  }
}