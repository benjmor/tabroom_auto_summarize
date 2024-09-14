# Lambda that scrapes tabroom for upcoming tournaments
# IAM Role for Lambda function
resource "aws_iam_role" "schedule_scrape_lambda_role" {
  name = "schedule_scrape_lambda_role"

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

resource "aws_iam_role_policy_attachment" "schedule_scrape_lambda_logging" {
  role       = aws_iam_role.schedule_scrape_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "schedule_scrape_lambda_permissions" {
  role   = aws_iam_role.schedule_scrape_lambda_role.id
  policy = data.aws_iam_policy_document.schedule_scrape_lambda_permissions.json
}

resource "aws_lambda_function" "schedule_scrape_lambda_function" {
  function_name = "schedule_scrape_lambda_function"
  runtime       = "python3.12"
  handler       = "batch_scrape_lambda.lambda_handler"
  role          = aws_iam_role.schedule_scrape_lambda_role.arn
  filename      = data.archive_file.schedule_scrape_lambda_source.output_path
  environment {
    variables = {
      DDB_TABLE_NAME = var.ddb_table_name
      SNS_TOPIC_ARN = var.sns_topic_arn
    }
  }
  source_code_hash = data.archive_file.schedule_scrape_lambda_source.output_base64sha256
  timeout          = 25
}

