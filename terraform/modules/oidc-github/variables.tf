variable "github_repository" {
  description = "GitHub repository in format owner/repo"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "quality-agent"
}
