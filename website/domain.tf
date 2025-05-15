resource "aws_route53domains_registered_domain" "tabroom_summary" {
    domain_name   = var.domain_name
    transfer_lock = false
}