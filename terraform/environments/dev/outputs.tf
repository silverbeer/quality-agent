output "webhook_function_url" {
  description = "Lambda Function URL for GitHub webhook"
  value       = module.webhook_receiver.function_url
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions"
  value       = module.oidc_github.github_actions_role_arn
}

output "events_bucket_name" {
  description = "S3 bucket for webhook events"
  value       = module.event_storage.events_bucket_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for CrewAI processor"
  value       = module.crewai_processor.ecr_repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.crewai_processor.ecs_cluster_name
}
