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