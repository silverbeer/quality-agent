# AWS Serverless Deployment

This directory contains Terraform infrastructure-as-code for deploying quality-agent to AWS serverless.

## Architecture

```
GitHub Webhooks (PR, push, workflow_run)
              │
              ▼
    ┌─────────────────────┐
    │ Lambda Function URL │  (Webhook Receiver)
    │ 256 MB, 30s timeout │
    └─────────┬───────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
   ┌─────────┐  ┌─────────┐
   │   S3    │  │   SQS   │
   │ Events  │  │  Queue  │
   └─────────┘  └────┬────┘
                     │
                     ▼
        ┌────────────────────┐
        │  Fargate Spot Task │  (CrewAI Processing)
        │  2 GB, no timeout  │
        └────────────────────┘
                     │
                     ▼
              CloudWatch Logs
```

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.5.0
3. GitHub repository with Actions enabled

## Initial Setup

### 1. Create Terraform Backend Resources

Before first deployment, create the S3 bucket and DynamoDB table for Terraform state:

```bash
# Create S3 bucket for state
aws s3api create-bucket \
  --bucket quality-agent-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket quality-agent-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name quality-agent-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 2. Create Secrets in Parameter Store

```bash
# GitHub webhook secret (generate a random string)
aws ssm put-parameter \
  --name "/quality-agent/dev/github-webhook-secret" \
  --type "SecureString" \
  --value "your-webhook-secret-here"

# Anthropic API key
aws ssm put-parameter \
  --name "/quality-agent/dev/anthropic-api-key" \
  --type "SecureString" \
  --value "sk-ant-your-key-here"

# GitHub token (with repo read access)
aws ssm put-parameter \
  --name "/quality-agent/dev/github-token" \
  --type "SecureString" \
  --value "ghp_your-token-here"
```

### 3. Bootstrap OIDC (One-time manual setup)

The first deployment must be done manually to create the OIDC provider and IAM role that GitHub Actions will use:

```bash
cd terraform/environments/dev

# Initialize and apply just the OIDC module first
terraform init
terraform apply -target=module.oidc_github

# Note the output role ARN
terraform output github_actions_role_arn
```

### 4. Configure GitHub Repository

1. Go to Settings → Secrets and variables → Actions
2. Add repository secret:
   - `AWS_ROLE_ARN`: The IAM role ARN from step 3

3. Go to Settings → Environments
4. Create environment: `dev`

### 5. Configure GitHub Webhook

After the first full deployment, get the webhook URL:

```bash
terraform output webhook_function_url
```

In your target repository (e.g., missing-table):
1. Go to Settings → Webhooks → Add webhook
2. Payload URL: The Lambda function URL
3. Content type: application/json
4. Secret: Same value as `/quality-agent/dev/github-webhook-secret`
5. Events: Select "Pull requests", "Pushes", "Workflow runs"

## Deployment

### Automated (via GitHub Actions)

- **PR to main**: Runs `terraform plan` and comments on PR
- **Push to main**: Runs `terraform apply` and builds images

### Manual

```bash
cd terraform/environments/dev

# Initialize
terraform init

# Plan
terraform plan

# Apply
terraform apply
```

## Modules

| Module | Description |
|--------|-------------|
| `oidc-github` | GitHub Actions OIDC provider and IAM role |
| `event-storage` | S3 bucket, SQS queues, DynamoDB table |
| `webhook-receiver` | Lambda function with Function URL |
| `crewai-processor` | ECR, ECS cluster, Fargate task definition |
| `monitoring` | CloudWatch alarms |

## Outputs

| Output | Description |
|--------|-------------|
| `webhook_function_url` | URL for GitHub webhook configuration |
| `github_actions_role_arn` | IAM role for GitHub Actions |
| `events_bucket_name` | S3 bucket for stored events |
| `ecr_repository_url` | ECR repository for processor image |

## Cost Estimate

For ~100 PRs/month:

| Service | Monthly Cost |
|---------|-------------|
| Lambda | $0 (free tier) |
| S3 | $0 (free tier) |
| SQS | $0 (free tier) |
| DynamoDB | $0 (free tier) |
| Fargate Spot | ~$2-3 |
| **Total** | **~$2-3** |

## Troubleshooting

### Lambda Function Not Found
If the Lambda doesn't exist yet, run `terraform apply` first to create infrastructure.

### OIDC Authentication Failed
Ensure the GitHub Actions role ARN is correctly set in repository secrets.

### Webhook Signature Failed
Verify the webhook secret matches between GitHub and Parameter Store.

### Fargate Task Not Starting
Check CloudWatch logs at `/ecs/quality-agent-processor-dev` for errors.

## Security

- All secrets stored in AWS Systems Manager Parameter Store
- GitHub Actions uses OIDC - no long-lived AWS credentials
- Webhook signature verification using HMAC SHA-256
- S3 bucket encryption enabled
- All IAM roles follow least-privilege principle
