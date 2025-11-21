output "ecr_repository_url" {
  description = "ECR repository URL for processor image"
  value       = aws_ecr_repository.processor.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.main.arn
}

output "task_definition_arn" {
  description = "ECS task definition ARN"
  value       = aws_ecs_task_definition.processor.arn
}

output "sqs_trigger_function_name" {
  description = "SQS trigger Lambda function name"
  value       = aws_lambda_function.sqs_trigger.function_name
}
