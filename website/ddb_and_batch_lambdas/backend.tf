# Assumes that DDB and S3 have been bootstrapped for TF usage

terraform {
  backend "s3" {
    encrypt        = "true"
    bucket         = "238589881750-tf-remote-state"
    dynamodb_table = "tf-state-lock"
    key            = "github.com/benjmor/tabroom_auto_summarize_batch_lambdas"
    region         = "us-east-1"
  }
}