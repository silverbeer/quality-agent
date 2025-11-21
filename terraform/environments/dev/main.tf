provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.tags, {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    })
  }
}

# GitHub Actions OIDC for CI/CD
module "oidc_github" {
  source = "../../modules/oidc-github"

  github_repository = var.github_repository
  environment       = var.environment
}

# Event storage (S3, SQS, DynamoDB)
module "event_storage" {
  source = "../../modules/event-storage"

  project_name = var.project_name
  environment  = var.environment
}

# Webhook receiver Lambda
module "webhook_receiver" {
  source = "../../modules/webhook-receiver"

  project_name                    = var.project_name
  environment                     = var.environment
  events_bucket_name              = module.event_storage.events_bucket_name
  events_bucket_arn               = module.event_storage.events_bucket_arn
  processing_queue_url            = module.event_storage.processing_queue_url
  processing_queue_arn            = module.event_storage.processing_queue_arn
  idempotency_table_name          = module.event_storage.idempotency_table_name
  idempotency_table_arn           = module.event_storage.idempotency_table_arn
  github_webhook_secret_parameter = var.github_webhook_secret_parameter
}

# CrewAI processor (Fargate Spot)
module "crewai_processor" {
  source = "../../modules/crewai-processor"

  project_name               = var.project_name
  environment                = var.environment
  aws_region                 = var.aws_region
  events_bucket_name         = module.event_storage.events_bucket_name
  events_bucket_arn          = module.event_storage.events_bucket_arn
  processing_queue_url       = module.event_storage.processing_queue_url
  processing_queue_arn       = module.event_storage.processing_queue_arn
  anthropic_api_key_parameter = var.anthropic_api_key_parameter
  github_token_parameter     = var.github_token_parameter
}

# Monitoring and alerts
module "monitoring" {
  source = "../../modules/monitoring"

  project_name                = var.project_name
  environment                 = var.environment
  webhook_lambda_name         = module.webhook_receiver.lambda_function_name
  processing_queue_name       = module.event_storage.processing_queue_name
  dlq_name                    = module.event_storage.dlq_name
  ecs_cluster_name            = module.crewai_processor.ecs_cluster_name
}
