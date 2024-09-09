data "aws_caller_identity" "current" {}
data "aws_region" "current" {}


data "archive_file" "lambda_source" {
  type        = "zip"
  source_file = "${path.module}/lambda/lambda_handler.py"
  output_path = "${path.module}/lambda/lambda_handler.zip"
}

data "aws_iam_policy_document" "public_website_access" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.website_bucket.arn,
      "${aws_s3_bucket.website_bucket.arn}/*",
    ]
  }
}

data "aws_iam_policy_document" "lambda_s3_writes" {
  statement {

    actions = [
      "s3:GetObject*",
      "s3:PutObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.data_bucket.arn,
      "${aws_s3_bucket.data_bucket.arn}/*",
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction",
    ]
    resources = [
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${local.summary_lambda_function_name}",
    ]
  }
  # TODO - scope down these permissions to just what is needed
  statement {
    actions = [
      "bedrock-runtime:*",
      "bedrock:*",
    ]
    resources = [
      "*",
    ]
  }
}

data "aws_iam_policy_document" "summmarizer_role" {
  statement {

    actions = [
      "s3:GetObject*",
      "s3:PutObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.data_bucket.arn,
      "${aws_s3_bucket.data_bucket.arn}/*",
    ]
  }

  statement {
    actions = [
      "sns:Publish",
      "secretsmanager:DeleteSecret",
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

  statement {
    actions = [
      "iam:PassRole"
    ]
    resources = [
      "arn:aws:iam::238589881750:role/summary_lambda_role"
    ]
    conditions {
      test     = "StringEquals"
      variable = "iam:PassedToService"

      values = [
        "lambda.amazonaws.com"
      ]
    }
  }
}

# data "archive_file" "summary_lambda_source" {
#   type        = "zip"
#   source_file = "${path.module}/summary_lambda/summary_generator.py"
#   output_path = "${path.module}/summary_lambda/summary_generator.zip"
# }

# resource "null_resource" "install_requirements" {
#   triggers = {
#     updated_at = timestamp()
#   }

#   provisioner "local-exec" {
#     interpreter = ["PowerShell", "-Command"] # Oh no, Windows! Deal with it.
#     command     = <<EOF
# Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass # Allow the script to run
# Remove-Item "${path.module}/../tabroom_summary/lambda_layer" -Recurse -Force -ErrorAction SilentlyContinue # Remove the old layer
# New-Item -ItemType Directory "${path.module}/../tabroom_summary/lambda_layer/python" -Force
# $env:PIP_USER=0
# pip install --platform manylinux_2_17_x86_64 --only-binary=:all: -r "${path.module}/../tabroom_summary/requirements.txt" -t "${path.module}/../tabroom_summary/lambda_layer/python"
# New-Item -ItemType Directory "${path.module}/../tabroom_summary/lambda_layer/python/tabroom_summary" -Force
# Copy-Item "${path.module}/../tabroom_summary/*.py" "${path.module}/../tabroom_summary/lambda_layer/python/tabroom_summary"
# New-Item -ItemType Directory "${path.module}/../tabroom_summary/lambda_layer/python/tabroom_summary/scraper" -Force
# Copy-Item "${path.module}/../tabroom_summary/scraper/*.py" "${path.module}/../tabroom_summary/lambda_layer/python/tabroom_summary/scraper"
# Remove-Item "${path.module}/../tabroom_summary/lambda_layer/python/tabroom_summary/openAiAuthKey.txt" -Force -ErrorAction SilentlyContinue
# exit 0
#       EOF

#     working_dir = "${path.module}/../tabroom_summary"
#   }
# }

# data "archive_file" "tabroom_summary_layer" {
#   depends_on  = [null_resource.install_requirements]
#   type        = "zip"
#   source_dir  = "${path.module}/../tabroom_summary/lambda_layer"
#   output_path = "${path.module}/tabroom_summary_layer.zip"
#   excludes    = ["*.pyc"]
# }