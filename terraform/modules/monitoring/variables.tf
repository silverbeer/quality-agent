variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "webhook_lambda_name" {
  description = "Webhook receiver Lambda function name"
  type        = string
}

variable "processing_queue_name" {
  description = "Processing queue name"
  type        = string
}

variable "dlq_name" {
  description = "Dead letter queue name"
  type        = string
}

variable "ecs_cluster_name" {
  description = "ECS cluster name"
  type        = string
}
