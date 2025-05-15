locals {
  account_id            = data.aws_caller_identity.current.account_id
  protected_branch_name = "main"
  # rvm_assumption_policy = jsonencode({
  #   "Version" : "2012-10-17",
  #   "Statement" : [
  #     {
  #       "Effect" : "Allow",
  #       "Action" : [
  #         "sts:TagSession",
  #         "sts:SetSourceIdentity",
  #         "sts:AssumeRole"
  #       ],
  #       "Resource" : [
  #         "arn:aws:iam::*:role/${var.iam_assuming_role_name}"
  #       ]
  #     }
  #   ]
  # })
  # rvm_readonly_assumption_policy = jsonencode({
  #   "Version" : "2012-10-17",
  #   "Statement" : [
  #     {
  #       "Effect" : "Allow",
  #       "Action" : [
  #         "sts:TagSession",
  #         "sts:SetSourceIdentity",
  #         "sts:AssumeRole"
  #       ],
  #       "Resource" : [
  #         "arn:aws:iam::*:role/${var.iam_assuming_role_name}-readonly"
  #       ]
  #     }
  #   ]
  # })
  tabroom_modify_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:*",
        ],
        "Resource" : [
          "arn:aws:s3:::tabroomsummary.com",
          "arn:aws:s3:::tabroomsummary.com/*",
          "arn:aws:s3:::docker-selenium-lambda-ta-serverlessdeploymentbuck-*",
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "lambda:*",
        ],
        "Resource" : [
          "arn:aws:lambda:us-east-1:238589881750:function:api_lambda_function",
          "arn:aws:lambda:us-east-1:238589881750:function:docker-selenium-lambda-tabroom-prod-main",
          "arn:aws:lambda:us-east-1:238589881750:function:schedule_scrape_lambda_function",
          "arn:aws:lambda:us-east-1:238589881750:function:batch_process_lambda_function",
          "arn:aws:lambda:us-east-1:238589881750:function:recent_summaries_lambda_function",
          "arn:aws:lambda:us-east-1:238589881750:function:email_results_lambda_function"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "ecr:*",
        ],
        "Resource" : [
          "arn:aws:ecr:us-east-1:238589881750:repository/serverless-docker-selenium-lambda-tabroom-prod"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "cloudformation:*",
        ],
        "Resource" : [
          "arn:aws:cloudformation:us-east-1:238589881750:stack/docker-selenium-lambda-tabroom-prod",
          "arn:aws:cloudformation:us-east-1:238589881750:stack/docker-selenium-lambda-tabroom-prod/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "events:PutRule",
          "events:PutTargets",
          "events:DeleteRule",
          "events:RemoveTargets"
        ],
        "Resource" : [
          "*",
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "ses:VerifyEmailIdentity",
          "acm:*",
          "cloudfront:*",
          "route53:*",
          "apigateway:*",
        ],
        "Resource" : [
          "*",
        ]
      },
            {
        "Effect" : "Allow",
        "Action" : [
          "iam:CreateRole",
          "iam:PutRolePolicy",
          "iam:PassRole",
          "iam:AttachRolePolicy"
        ],
        "Resource" : [
          "arn:aws:iam::238589881750:role/ses_notify_role",
          "arn:aws:iam::238589881750:role/summary_lambda_role",
        ],
        "Condition": {
          "StringLikeIfExists": {
            "iam:PassedToService": "lambda.amazonaws.com"
          }
        }
      }
    ]
  })
  terraform_state_policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
        ],
        "Resource" : [
          "arn:aws:s3:::${local.account_id}-${var.bucket_suffix}",
          "arn:aws:s3:::${local.account_id}-${var.bucket_suffix}/*",
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ],
        "Resource" : [
          "arn:aws:dynamodb:*:${local.account_id}:table/${var.ddb_lock_table_name}"
        ]
      }
    ]
  })
}
