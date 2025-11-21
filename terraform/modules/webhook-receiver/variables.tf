variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "events_bucket_name" {
  description = "S3 bucket name for storing events"
  type        = string
}

variable "events_bucket_arn" {
  description = "S3 bucket ARN for storing events"
  type        = string
}

variable "processing_queue_url" {
  description = "SQS queue URL for processing messages"
  type        = string
}

variable "processing_queue_arn" {
  description = "SQS queue ARN for processing messages"
  type        = string
}

variable "idempotency_table_name" {
  description = "DynamoDB table name for idempotency"
  type        = string
}

variable "idempotency_table_arn" {
  description = "DynamoDB table ARN for idempotency"
  type        = string
}

variable "github_webhook_secret_parameter" {
  description = "SSM Parameter Store name for GitHub webhook secret"
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to Lambda deployment package"
  type        = string
  default     = "../../../dist/webhook_receiver.zip"
}

variable "lambda_zip_hash" {
  description = "Base64-encoded SHA256 hash of Lambda package"
  type        = string
  default     = ""
}
