# Webhook Receiver Lambda Module
# Lambda with Function URL to receive GitHub webhooks

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# IAM Role for Lambda
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-webhook-receiver-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Lambda execution policy
resource "aws_iam_role_policy" "lambda" {
  name = "lambda-execution"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-webhook-receiver-${var.environment}:*"
      },
      # S3 for storing events
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${var.events_bucket_arn}/*"
      },
      # SQS for sending messages
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.processing_queue_arn
      },
      # DynamoDB for idempotency
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = var.idempotency_table_arn
      },
      # SSM Parameter Store for webhook secret
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.github_webhook_secret_parameter}"
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-webhook-receiver-${var.environment}"
  retention_in_days = 14
}

# Lambda function
resource "aws_lambda_function" "webhook_receiver" {
  function_name = "${var.project_name}-webhook-receiver-${var.environment}"
  role          = aws_iam_role.lambda.arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 256

  filename         = var.lambda_zip_path
  source_code_hash = var.lambda_zip_hash

  environment {
    variables = {
      ENVIRONMENT                     = var.environment
      EVENTS_BUCKET                   = var.events_bucket_name
      PROCESSING_QUEUE_URL            = var.processing_queue_url
      IDEMPOTENCY_TABLE               = var.idempotency_table_name
      GITHUB_WEBHOOK_SECRET_PARAMETER = var.github_webhook_secret_parameter
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda
  ]
}

# Lambda Function URL
resource "aws_lambda_function_url" "webhook" {
  function_name      = aws_lambda_function.webhook_receiver.function_name
  authorization_type = "NONE"  # GitHub webhooks don't support AWS IAM auth

  cors {
    allow_origins = ["*"]
    allow_methods = ["POST"]
    allow_headers = ["*"]
    max_age       = 86400
  }
}

# Allow Lambda to be invoked via Function URL
resource "aws_lambda_permission" "function_url" {
  statement_id           = "AllowFunctionURLInvoke"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.webhook_receiver.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}
