module "network" {
  source        = "../../modules/network"
  region        = var.region
  environment   = var.environment
  private_cidrs = ["10.40.0.0/16"]
}

module "kubernetes" {
  source       = "../../modules/kubernetes"
  region       = var.region
  environment  = var.environment
  cluster_name = "safelytold-dev"
}

module "postgres" {
  source         = "../../modules/postgres"
  region         = var.region
  environment    = var.environment
  database_names = ["case", "evidence", "privacy", "analytics"]
}

module "identity_vault" {
  source         = "../../modules/identity_vault"
  region         = var.region
  environment    = var.environment
  administrators = []
}

module "audit_store" {
  source         = "../../modules/audit_store"
  region         = var.region
  environment    = var.environment
  retention_days = 2555
}

module "object_storage" {
  source         = "../../modules/object_storage"
  region         = var.region
  environment    = var.environment
  retention_days = 2555
}

module "messaging" {
  source      = "../../modules/messaging"
  region      = var.region
  environment = var.environment
  quorum_size = 3
}

module "temporal" {
  source      = "../../modules/temporal"
  region      = var.region
  environment = var.environment
  namespace   = "safelytold-dev"
}

module "prefect" {
  source         = "../../modules/prefect"
  region         = var.region
  environment    = var.environment
  work_pool_name = "safelytold-dev"
}

module "key_management" {
  source             = "../../modules/key_management"
  region             = var.region
  environment        = var.environment
  key_administrators = []
}

module "observability" {
  source         = "../../modules/observability"
  region         = var.region
  environment    = var.environment
  retention_days = 30
}

module "blockchain" {
  source          = "../../modules/blockchain"
  region          = var.region
  environment     = var.environment
  validator_count = 4
}
