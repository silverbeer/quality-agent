# CrewAI Processor Fargate Module
# ECS Fargate Spot tasks for running CrewAI analysis

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Archive for SQS trigger Lambda
data "archive_file" "sqs_trigger" {
  type        = "zip"
  source_file = "${path.module}/sqs_trigger_code/index.py"
  output_path = "${path.module}/sqs_trigger.zip"
}

# ECR Repository for CrewAI processor image
resource "aws_ecr_repository" "processor" {
  name                 = "${var.project_name}-processor-${var.environment}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ECR Lifecycle policy to manage images
resource "aws_ecr_lifecycle_policy" "processor" {
  repository = aws_ecr_repository.processor.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "disabled"  # Free tier optimization
  }
}

# ECS Cluster Capacity Providers (Fargate Spot)
resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE_SPOT", "FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 100
    base              = 0
  }
}

# CloudWatch Log Group for ECS tasks
resource "aws_cloudwatch_log_group" "processor" {
  name              = "/ecs/${var.project_name}-processor-${var.environment}"
  retention_in_days = 14
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "task_execution" {
  name = "${var.project_name}-task-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Additional policy for Parameter Store access
resource "aws_iam_role_policy" "task_execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.anthropic_api_key_parameter}",
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.github_token_parameter}"
        ]
      }
    ]
  })
}

# IAM Role for ECS Task (application role)
resource "aws_iam_role" "task" {
  name = "${var.project_name}-task-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "task" {
  name = "task-permissions"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # S3 for reading events and storing results
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${var.events_bucket_arn}/*"
      },
      # SQS for receiving messages
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.processing_queue_arn
      },
      # CloudWatch Logs
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.processor.arn}:*"
      }
    ]
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "processor" {
  family                   = "${var.project_name}-processor-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512  # 0.5 vCPU
  memory                   = 2048 # 2 GB
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "processor"
      image     = "${aws_ecr_repository.processor.repository_url}:latest"
      essential = true

      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "EVENTS_BUCKET"
          value = var.events_bucket_name
        },
        {
          name  = "PROCESSING_QUEUE_URL"
          value = var.processing_queue_url
        }
      ]

      secrets = [
        {
          name      = "ANTHROPIC_API_KEY"
          valueFrom = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.anthropic_api_key_parameter}"
        },
        {
          name      = "GITHUB_TOKEN"
          valueFrom = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter${var.github_token_parameter}"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.processor.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "processor"
        }
      }
    }
  ])
}

# Lambda to trigger Fargate tasks from SQS
resource "aws_iam_role" "sqs_trigger" {
  name = "${var.project_name}-sqs-trigger-${var.environment}"

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

resource "aws_iam_role_policy" "sqs_trigger" {
  name = "sqs-trigger-permissions"
  role = aws_iam_role.sqs_trigger.id

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
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.project_name}-sqs-trigger-${var.environment}:*"
      },
      # SQS for reading messages
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.processing_queue_arn
      },
      # ECS for running tasks
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = aws_ecs_task_definition.processor.arn
      },
      # IAM for passing roles to ECS
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.task_execution.arn,
          aws_iam_role.task.arn
        ]
      },
      # EC2 for network interfaces (Fargate requirement)
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group for SQS trigger Lambda
resource "aws_cloudwatch_log_group" "sqs_trigger" {
  name              = "/aws/lambda/${var.project_name}-sqs-trigger-${var.environment}"
  retention_in_days = 14
}

# Get default VPC and subnets for Fargate tasks
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group for Fargate tasks
resource "aws_security_group" "processor" {
  name        = "${var.project_name}-processor-${var.environment}"
  description = "Security group for CrewAI processor tasks"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Lambda function to trigger Fargate tasks
resource "aws_lambda_function" "sqs_trigger" {
  function_name = "${var.project_name}-sqs-trigger-${var.environment}"
  role          = aws_iam_role.sqs_trigger.arn
  handler       = "index.handler"
  runtime       = "python3.13"
  timeout       = 30
  memory_size   = 128

  filename         = data.archive_file.sqs_trigger.output_path
  source_code_hash = data.archive_file.sqs_trigger.output_base64sha256

  environment {
    variables = {
      ECS_CLUSTER         = aws_ecs_cluster.main.name
      TASK_DEFINITION     = aws_ecs_task_definition.processor.arn
      SUBNETS             = join(",", data.aws_subnets.default.ids)
      SECURITY_GROUPS     = aws_security_group.processor.id
      CONTAINER_NAME      = "processor"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.sqs_trigger
  ]
}

# SQS Event Source Mapping
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = var.processing_queue_arn
  function_name    = aws_lambda_function.sqs_trigger.arn
  batch_size       = 1
  enabled          = true
}
