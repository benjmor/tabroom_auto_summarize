data "aws_caller_identity" "current" {}
data "aws_region" "current" {}


data "archive_file" "lambda_source" {
  type        = "zip"
  source_file = "${path.module}/lambda/lambda_handler.py"
  output_path = "${path.module}/lambda/lambda_handler.zip"
}

data "aws_iam_policy_document" "public_website_access" {
  depends_on = [ aws_cloudfront_distribution.prod_distribution ]
  statement {
    actions = [
      "s3:GetObject"
    ]
    principals {
      identifiers = [
      aws_cloudfront_origin_access_identity.origin_access_identity.iam_arn]
      type = "AWS"
    }
    resources = ["arn:aws:s3:::site-${var.domain_name}/*"]
  }
  
  statement {
    actions = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::site-${var.domain_name}"]
    principals {
      type = "AWS"
      identifiers = [aws_cloudfront_origin_access_identity.origin_access_identity.iam_arn]
    }
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
    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"

      values = [
        "lambda.amazonaws.com"
      ]
    }
  }

  statement {
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.email_results_lambda_function_name}",
    ]
  }
}
