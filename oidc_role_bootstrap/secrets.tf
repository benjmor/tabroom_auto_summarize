# Create two secrets, TABROOM_USERNAME and TABROOM_PASSWORD
# as AWS Secrets Manager secrets, but do not update their values

resource "aws_secretsmanager_secret" "tabroom_username" {
  name = "TABROOM_USERNAME"
  lifecycle {
    ignore_changes = all
  }
}

resource "aws_secretsmanager_secret" "tabroom_password" {
  name = "TABROOM_PASSWORD"
  lifecycle {
    ignore_changes = all
  }
}
