# Create the Lambda Role
resource "aws_iam_role" "ses_notify_role" {
  name = "ses_notify_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role = aws_iam_role.ses_notify_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy" "inline" {
    role = aws_iam_role.ses_notify_role.name
    policy = data.aws_iam_policy_document.lambda_ses_and_invoke.json
}
# Create the Lambda itself
resource "aws_lambda_function" "email_results_lambda_function" {
  function_name = "email_results_lambda_function"
  runtime       = "python3.12"
  handler       = "lambda_handler.lambda_handler"
  role          = aws_iam_role.ses_notify_role.arn
  filename      = data.archive_file.ses_lambda_handler_source.output_path
#   environment {
#     variables = {
#     }
#   }
  source_code_hash = data.archive_file.ses_lambda_handler_source.output_base64sha256
  timeout          = 58 # Needs to run longer but API Gateway could still time out at 30s unless we adapt: https://aws.amazon.com/about-aws/whats-new/2024/06/amazon-api-gateway-integration-timeout-limit-29-seconds/
}

# Create the SES record -- will need manual verification and manual request to move SES from Sandbox to Production mode
resource "aws_ses_email_identity" "example" {
  email = var.sender_email
}