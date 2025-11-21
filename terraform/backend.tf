# Backend configuration for Terraform state
#
# Before first use, you need to create the S3 bucket and DynamoDB table:
#
# aws s3api create-bucket --bucket quality-agent-terraform-state --region us-east-1
# aws s3api put-bucket-versioning --bucket quality-agent-terraform-state --versioning-configuration Status=Enabled
# aws dynamodb create-table \
#   --table-name quality-agent-terraform-locks \
#   --attribute-definitions AttributeName=LockID,AttributeType=S \
#   --key-schema AttributeName=LockID,KeyType=HASH \
#   --billing-mode PAY_PER_REQUEST

terraform {
  backend "s3" {
    bucket         = "quality-agent-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "quality-agent-terraform-locks"
    encrypt        = true
  }
}
