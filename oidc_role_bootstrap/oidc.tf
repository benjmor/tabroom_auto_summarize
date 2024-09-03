# Create the OIDC role used by the GitHub stuff

module "oidc" {
    source              = "./oidc_provider"
    github_organization = "benjmor"
}