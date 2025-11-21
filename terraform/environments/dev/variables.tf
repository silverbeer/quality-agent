variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "quality-agent"
}

variable "github_repository" {
  description = "GitHub repository in format owner/repo"
  type        = string
  default     = "silverbeer/quality-agent"
}

variable "github_webhook_secret_parameter" {
  description = "SSM Parameter Store name for GitHub webhook secret"
  type        = string
  default     = "/quality-agent/dev/github-webhook-secret"
}

variable "anthropic_api_key_parameter" {
  description = "SSM Parameter Store name for Anthropic API key"
  type        = string
  default     = "/quality-agent/dev/anthropic-api-key"
}

variable "github_token_parameter" {
  description = "SSM Parameter Store name for GitHub token"
  type        = string
  default     = "/quality-agent/dev/github-token"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
