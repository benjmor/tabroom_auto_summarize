variable "ddb_table_name" {
    type = string
    default = "tabroom_tournaments"
    description = "The name of the DDB table to store the tournament metadata."
}

variable "sns_topic_arn" {
    type = string
    default = "arn:aws:sns:us-east-1:238589881750:summary_generation_topic"
    description = "The name of the SNS topic to ping if the Lambda(s) have results to share."
}