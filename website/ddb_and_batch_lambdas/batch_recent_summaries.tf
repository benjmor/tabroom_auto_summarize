# Lambda that creates a text table with the newest tournaments, then sends it to S3
# IAM Role for Lambda function
resource "aws_iam_role" "recent_summaries_lambda_role" {
  name = "recent_summaries_lambda_role"

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

resource "aws_iam_role_policy_attachment" "recent_summaries_lambda_logging" {
  role       = aws_iam_role.recent_summaries_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "recent_summaries_lambda_permissions" {
  role   = aws_iam_role.recent_summaries_lambda_role.id
  policy = data.aws_iam_policy_document.recent_summaries_lambda_permissions.json
}

resource "aws_lambda_function" "recent_summaries_lambda_function" {
  function_name = "recent_summaries_lambda_function"
  runtime       = "python3.12"
  handler       = "recent_summaries_lambda.lambda_handler"
  role          = aws_iam_role.recent_summaries_lambda_role.arn
  filename      = data.archive_file.recent_summaries_lambda_source.output_path
  environment {
    variables = {
      BUCKET_TARGET = "tabroomsummary.com"
      DDB_NAME = var.ddb_table_name
    }
  }
  source_code_hash = data.archive_file.recent_summaries_lambda_source.output_base64sha256
  timeout          = 25
}