data "archive_file" "claude_lambda_source" {
  type        = "zip"
  source_file = "${path.module}/claude_test.py"
  output_path = "${path.module}/claude_test.zip"
}

resource "aws_iam_role" "claude_lambda_role" {
  name = "claude_lambda_execution_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com",
        },
      },
    ],
  })
}

resource "aws_iam_role_policy_attachment" "claude_admin_lambda" {
  role       = aws_iam_role.claude_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_lambda_function" "claude_test" {
  function_name    = "claude_test"
  runtime          = "python3.12"
  handler          = "claude_test.usage_demo"
  role             = aws_iam_role.claude_lambda_role.arn
  filename         = data.archive_file.claude_lambda_source.output_path
  source_code_hash = data.archive_file.claude_lambda_source.output_base64sha256
  timeout          = 10
}

provider "aws" {
  region = "us-east-1" # Replace with your desired AWS region
}