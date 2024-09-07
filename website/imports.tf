import {
  to = aws_s3_bucket.website_bucket
  id = "tabroomsummary.com"
}

import {
  to = aws_route53domains_registered_domain.tabroom_summary
  id = "tabroomsummary.com"
}

import {
    to = module.ddb_and_batch_lambdas.aws_dynamodb_table.tabroom_tournaments
    id = "tabroom_tournaments"
}