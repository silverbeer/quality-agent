#!/bin/bash
# Bootstrap script for AWS Terraform backend and initial secrets
#
# This script creates:
# 1. S3 bucket for Terraform state
# 2. DynamoDB table for state locking
# 3. Parameter Store entries for secrets (prompts for values)
#
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - Permissions to create S3, DynamoDB, and SSM resources

set -euo pipefail

# Configuration
PROJECT_NAME="${PROJECT_NAME:-quality-agent}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

# Derived names
STATE_BUCKET="${PROJECT_NAME}-terraform-state"
LOCK_TABLE="${PROJECT_NAME}-terraform-locks"

echo "=========================================="
echo "Quality Agent - AWS Bootstrap"
echo "=========================================="
echo ""
echo "Project:     ${PROJECT_NAME}"
echo "Region:      ${AWS_REGION}"
echo "Environment: ${ENVIRONMENT}"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "AWS Account: ${ACCOUNT_ID}"
echo ""

# Confirm before proceeding
read -p "Continue with bootstrap? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Step 1: Creating S3 bucket for Terraform state..."
echo "------------------------------------------------"

if aws s3api head-bucket --bucket "${STATE_BUCKET}" 2>/dev/null; then
    echo "✓ Bucket ${STATE_BUCKET} already exists"
else
    # Create bucket (us-east-1 doesn't need LocationConstraint)
    if [ "${AWS_REGION}" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "${STATE_BUCKET}" \
            --region "${AWS_REGION}"
    else
        aws s3api create-bucket \
            --bucket "${STATE_BUCKET}" \
            --region "${AWS_REGION}" \
            --create-bucket-configuration LocationConstraint="${AWS_REGION}"
    fi
    echo "✓ Created bucket ${STATE_BUCKET}"
fi

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket "${STATE_BUCKET}" \
    --versioning-configuration Status=Enabled
echo "✓ Enabled versioning on ${STATE_BUCKET}"

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket "${STATE_BUCKET}" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
echo "✓ Enabled encryption on ${STATE_BUCKET}"

# Block public access
aws s3api put-public-access-block \
    --bucket "${STATE_BUCKET}" \
    --public-access-block-configuration '{
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }'
echo "✓ Blocked public access on ${STATE_BUCKET}"

echo ""
echo "Step 2: Creating DynamoDB table for state locking..."
echo "----------------------------------------------------"

if aws dynamodb describe-table --table-name "${LOCK_TABLE}" --region "${AWS_REGION}" 2>/dev/null; then
    echo "✓ Table ${LOCK_TABLE} already exists"
else
    aws dynamodb create-table \
        --table-name "${LOCK_TABLE}" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "${AWS_REGION}"
    echo "✓ Created table ${LOCK_TABLE}"

    # Wait for table to be active
    echo "  Waiting for table to be active..."
    aws dynamodb wait table-exists --table-name "${LOCK_TABLE}" --region "${AWS_REGION}"
    echo "✓ Table is active"
fi

echo ""
echo "Step 3: Setting up Parameter Store secrets..."
echo "---------------------------------------------"
echo ""
echo "You'll be prompted for secret values. Leave blank to skip."
echo ""

# GitHub Webhook Secret
PARAM_WEBHOOK="/${PROJECT_NAME}/${ENVIRONMENT}/github-webhook-secret"
read -p "GitHub Webhook Secret (generate random string): " -s WEBHOOK_SECRET
echo
if [ -n "${WEBHOOK_SECRET}" ]; then
    aws ssm put-parameter \
        --name "${PARAM_WEBHOOK}" \
        --type "SecureString" \
        --value "${WEBHOOK_SECRET}" \
        --overwrite \
        --region "${AWS_REGION}" > /dev/null
    echo "✓ Set ${PARAM_WEBHOOK}"
else
    echo "⊘ Skipped ${PARAM_WEBHOOK}"
fi

# Anthropic API Key
PARAM_ANTHROPIC="/${PROJECT_NAME}/${ENVIRONMENT}/anthropic-api-key"
read -p "Anthropic API Key (sk-ant-...): " -s ANTHROPIC_KEY
echo
if [ -n "${ANTHROPIC_KEY}" ]; then
    aws ssm put-parameter \
        --name "${PARAM_ANTHROPIC}" \
        --type "SecureString" \
        --value "${ANTHROPIC_KEY}" \
        --overwrite \
        --region "${AWS_REGION}" > /dev/null
    echo "✓ Set ${PARAM_ANTHROPIC}"
else
    echo "⊘ Skipped ${PARAM_ANTHROPIC}"
fi

# GitHub Token
PARAM_GITHUB="/${PROJECT_NAME}/${ENVIRONMENT}/github-token"
read -p "GitHub Token (ghp_... with repo read): " -s GITHUB_TOKEN
echo
if [ -n "${GITHUB_TOKEN}" ]; then
    aws ssm put-parameter \
        --name "${PARAM_GITHUB}" \
        --type "SecureString" \
        --value "${GITHUB_TOKEN}" \
        --overwrite \
        --region "${AWS_REGION}" > /dev/null
    echo "✓ Set ${PARAM_GITHUB}"
else
    echo "⊘ Skipped ${PARAM_GITHUB}"
fi

echo ""
echo "=========================================="
echo "Bootstrap Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Initialize and apply OIDC module:"
echo "   cd terraform/environments/dev"
echo "   terraform init"
echo "   terraform apply -target=module.oidc_github"
echo ""
echo "2. Get the GitHub Actions role ARN:"
echo "   terraform output github_actions_role_arn"
echo ""
echo "3. Add to GitHub repository secrets:"
echo "   Settings → Secrets → Actions → New repository secret"
echo "   Name: AWS_ROLE_ARN"
echo "   Value: <the ARN from step 2>"
echo ""
echo "4. Apply full infrastructure:"
echo "   terraform apply"
echo ""
echo "5. Configure webhook in target repository with:"
echo "   terraform output webhook_function_url"
echo ""
