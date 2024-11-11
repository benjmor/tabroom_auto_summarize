data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "lambda_ses_and_invoke" {
  statement {

    actions = [
      "ses:SendRawEmail",
      "ses:SendEmail",
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
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.lambda_api_name}",
    ]
  }
}

data "archive_file" "ses_lambda_handler_source" {
  type        = "zip"
  source_file = "${path.module}/src/lambda_handler.py"
  output_path = "${path.module}/src/lambda_handler.zip"
}