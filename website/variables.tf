variable "read_only" {
    type = bool
    default = false
    description = "If true, the script will generate LLM prompts but not actually send them to the LLM."
}

variable "sender_email" {
    type = string
    description = "The email used to send completed summaries to requesters."
}

variable "lambda_api_name" {
    type = string
    description = "The name of the lambda function that processes API requests from the website."
}

variable "domain_name" {
    type = string
    description = "The domain name of the website."
}

variable "email_results_lambda_function_name" {
    type = string
    description = "The name of the lambda function that sends emails."
    default = "email_results_lambda_function"
}