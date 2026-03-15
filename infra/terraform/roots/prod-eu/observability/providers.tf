# PRODUCTION: Auth must use OIDC-based workload identity.
# DO NOT use developer credentials for production state access.

provider "kubernetes" {}
provider "helm" { kubernetes {} }
