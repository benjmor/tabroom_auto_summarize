# Outputs
output "website_url" {
  value = aws_s3_bucket_website_configuration.website_bucket.website_endpoint
}

output "api_gateway_url" {
  value = aws_api_gateway_stage.prod.invoke_url
}