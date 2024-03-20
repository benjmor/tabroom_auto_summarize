#########################################################
# WEBSITE BUCKET - S3 Bucket for the website content
#########################################################
resource "aws_s3_bucket" "website_bucket" {
  bucket = local.website_bucket_name
}

resource "aws_s3_bucket_public_access_block" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "website_bucket" {
  bucket = aws_s3_bucket.website_bucket.id
  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_object" "website_homepage" {
  depends_on = [aws_s3_bucket.website_bucket]
  bucket     = local.website_bucket_name
  key        = "index.html"
  source     = "${path.module}/index.html"
  etag       = filemd5("${path.module}/index.html")

  content_type = "text/html"
}

resource "aws_s3_bucket_policy" "public_access_to_website" {
  depends_on = [aws_s3_bucket_public_access_block.website_bucket]
  bucket     = aws_s3_bucket.website_bucket.id
  policy     = data.aws_iam_policy_document.public_website_access.json
}

resource "aws_s3_bucket_cors_configuration" "example" {
  bucket = aws_s3_bucket.website_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }

  cors_rule {
    allowed_methods = ["GET"]
    allowed_origins = ["*"]
  }
}

resource "aws_route53_zone" "exampleDomain" {
  name = local.domain_name
}

resource "aws_route53_record" "exampleDomain-a" {
  zone_id = aws_route53_zone.exampleDomain.zone_id
  name    = local.domain_name
  type    = "A"
  alias {
    name                   = aws_s3_bucket_website_configuration.website_bucket.website_endpoint
    zone_id                = aws_s3_bucket.website_bucket.hosted_zone_id
    evaluate_target_health = true
  }
}

#########################################################
# DATA BUCKET - S3 Bucket for the underlying data
#########################################################
resource "aws_s3_bucket" "data_bucket" {
  bucket = local.data_bucket_name
}

#############################################################
# Synchronous Lambda function to handle API Gateway requests
#############################################################
# IAM Role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"

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

resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_writes" {
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_s3_writes.json
}

resource "aws_lambda_function" "api_lambda_function" {
  function_name = "api_lambda_function"
  runtime       = "python3.12"
  handler       = "lambda_handler.lambda_handler"
  role          = aws_iam_role.lambda_role.arn
  filename      = data.archive_file.lambda_source.output_path
  environment {
    variables = {
      DATA_BUCKET_NAME = local.data_bucket_name
      TABROOM_SUMMARY_LAMBDA_NAME = local.summary_lambda_function_name
      READ_ONLY = var.read_only
    }
  }
  source_code_hash = data.archive_file.lambda_source.output_base64sha256
  timeout          = 25 # Steer clear of API GW's 30 second timeout
}

resource "aws_api_gateway_rest_api" "website_api" {
  name        = "website_api"
  description = "API for the website"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_resource" "api_resource" {
  rest_api_id = aws_api_gateway_rest_api.website_api.id
  parent_id   = aws_api_gateway_rest_api.website_api.root_resource_id
  path_part   = "submit_tournament"
}

resource "aws_api_gateway_method" "api_method" {
  rest_api_id   = aws_api_gateway_rest_api.website_api.id
  resource_id   = aws_api_gateway_resource.api_resource.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "method_response" {
  rest_api_id = aws_api_gateway_rest_api.website_api.id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.api_method.http_method
  status_code = "200"
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "api_integration" {
  rest_api_id             = aws_api_gateway_rest_api.website_api.id
  resource_id             = aws_api_gateway_resource.api_resource.id
  http_method             = aws_api_gateway_method.api_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_lambda_function.invoke_arn
}

resource "aws_api_gateway_integration_response" "api_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.website_api.id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.api_method.http_method
  status_code = aws_api_gateway_method_response.method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'*'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

resource "aws_lambda_permission" "api_lambda_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_lambda_function.arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.website_api.execution_arn}/*/*"
}

# Deploy the API Gateway
resource "aws_api_gateway_deployment" "api_gateway_deployment" {
  depends_on  = [aws_api_gateway_integration.api_integration]
  rest_api_id = aws_api_gateway_rest_api.website_api.id
  stage_name  = "prod"
}

#########################################################
# Asynchronous Lambda function to handle summary generation
#########################################################

# This is now deployed via Serverless but we still need the role
  resource "aws_iam_role" "summary_lambda_role" {
  name = "summary_lambda_role"

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

resource "aws_iam_role_policy_attachment" "summary_lambda_role" {
  role       = aws_iam_role.summary_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "summary_lambda_role" {
  role   = aws_iam_role.summary_lambda_role.id
  policy = data.aws_iam_policy_document.summmarizer_role.json
}

resource "aws_secretsmanager_secret" "openai_auth_key" {
  name = local.openai_auth_key_secret_name
  # Must update manually
  lifecycle {
    ignore_changes = all
  }
}

# Topic that notifies subscribers when a summary is requested
resource "aws_sns_topic" "summary_generation_topic" {
  name = "summary_generation_topic"
}