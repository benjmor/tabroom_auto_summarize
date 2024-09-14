# Lambda that reviews recently-completed tournaments to see if there's results, then sends them to the parser
# IAM Role for Lambda function
resource "aws_iam_role" "batch_process_lambda_role" {
  name = "batch_process_lambda_role"

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

resource "aws_iam_role_policy_attachment" "batch_process_lambda_logging" {
  role       = aws_iam_role.batch_process_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "batch_process_lambda_permissions" {
  role   = aws_iam_role.batch_process_lambda_role.id
  policy = data.aws_iam_policy_document.batch_process_lambda_permissions.json
}

resource "aws_lambda_function" "batch_process_lambda_function" {
  function_name = "batch_process_lambda_function"
  runtime       = "python3.12"
  handler       = "batch_process_lambda.lambda_handler"
  role          = aws_iam_role.batch_process_lambda_role.arn
  filename      = data.archive_file.batch_process_lambda_source.output_path
  environment {
    variables = {
      TARGET_TABROOM_SUMMARY_LAMBDA = "docker-selenium-lambda-tabroom-prod-main"
      DDB_NAME = var.ddb_table_name
    }
  }
  source_code_hash = data.archive_file.batch_process_lambda_source.output_base64sha256
  timeout          = 25
}