# Scrape new tournaments on the first day of each month
# Create the EventBridge rule
resource "aws_cloudwatch_event_rule" "monthly_trigger" {
  name                = "lambda-monthly-trigger"
  description         = "Triggers Lambda at 3 AM on the first day of every month"
  schedule_expression = "cron(0 11 1 * ? *)"  # 9 AM UTC on the 1st day of every month
}

# Add the target for the rule (your existing Lambda function)
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.monthly_trigger.name
  target_id = "LambdaMonthlyTarget"
  arn       = aws_lambda_function.schedule_scrape_lambda_function.arn  # Reference to your Lambda function
}

# Allow EventBridge to invoke your Lambda function
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.schedule_scrape_lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monthly_trigger.arn
}
# Run the batch processing Lambda on Mondays and Tuesdays each week at 1AM
# Create the EventBridge rule for Mondays and Tuesdays at 1 AM
resource "aws_cloudwatch_event_rule" "monday_tuesday_trigger" {
  name                = "lambda-monday-tuesday-trigger"
  description         = "Triggers Lambda at 1 AM every Monday and Tuesday"
  schedule_expression = "cron(0 9 ? * 2,3 *)"  # 1 AM UTC on Mondays (2) and Tuesdays (3)
}

# Add the target for the rule (your existing Lambda function)
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.monday_tuesday_trigger.name
  target_id = "LambdaMondayTuesdayTarget"
  arn       = aws_lambda_function.batch_process_lambda_function.arn  # Reference to your Lambda function
}

# Allow EventBridge to invoke your Lambda function
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeMondayTuesday"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.batch_process_lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monday_tuesday_trigger.arn
}



# Update the S3 bucket Mondays and Tuesdays each week at 2AM

resource "aws_cloudwatch_event_rule" "monday_tuesday_trigger_later" {
  name                = "lambda-monday-tuesday-trigger-later"
  description         = "Triggers Lambda at 1 AM every Monday and Tuesday"
  schedule_expression = "cron(0 10 ? * 2,3 *)"  # 1 AM UTC on Mondays (2) and Tuesdays (3)
}

# Add the target for the rule (your existing Lambda function)
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.monday_tuesday_trigger_later.name
  target_id = "LambdaMondayTuesdayTarget"
  arn       = aws_lambda_function.recent_summaries_lambda_function.arn  # Reference to your Lambda function
}

# Allow EventBridge to invoke your Lambda function
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeMondayTuesday"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.recent_summaries_lambda_function.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monday_tuesday_trigger_later.arn
}