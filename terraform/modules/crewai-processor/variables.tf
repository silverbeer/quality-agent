variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "events_bucket_name" {
  description = "S3 bucket name for events"
  type        = string
}

variable "events_bucket_arn" {
  description = "S3 bucket ARN for events"
  type        = string
}

variable "processing_queue_url" {
  description = "SQS queue URL for processing"
  type        = string
}

variable "processing_queue_arn" {
  description = "SQS queue ARN for processing"
  type        = string
}

variable "anthropic_api_key_parameter" {
  description = "SSM Parameter Store name for Anthropic API key"
  type        = string
}

variable "github_token_parameter" {
  description = "SSM Parameter Store name for GitHub token"
  type        = string
}
