resource "aws_dynamodb_table" "tabroom_tournaments" {
  name         = "tabroom_tournaments"
  billing_mode = "PAY_PER_REQUEST"  # or "PROVISIONED" for provisioned throughput

  hash_key      = "tourn_id"  # Replace with your primary key attribute name
  range_key     = "end_date"  # Optional: replace with your sort key attribute name

  attribute {
    name = "tourn_id"
    type = "S"  # String type
  }

  attribute {
    name = "end_date"  # Optional: define this if using a range key
    type = "S"  # String type
  }

  tags = {
    Name = "tabroom_tournaments"
  }
}

