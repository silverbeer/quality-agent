# Event Storage Module
# S3 bucket for webhook events, SQS for processing queue, DynamoDB for idempotency

# S3 Bucket for webhook events
resource "aws_s3_bucket" "events" {
  bucket = "${var.project_name}-events-${var.environment}"
}

resource "aws_s3_bucket_versioning" "events" {
  bucket = aws_s3_bucket.events.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "events" {
  bucket = aws_s3_bucket.events.id

  rule {
    id     = "expire-old-events"
    status = "Enabled"

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "events" {
  bucket = aws_s3_bucket.events.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "events" {
  bucket = aws_s3_bucket.events.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Dead Letter Queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 days

  tags = {
    Name = "${var.project_name}-dlq-${var.environment}"
  }
}

# Main processing queue
resource "aws_sqs_queue" "processing" {
  name                       = "${var.project_name}-processing-${var.environment}"
  visibility_timeout_seconds = 900  # 15 minutes (match Lambda timeout)
  message_retention_seconds  = 345600  # 4 days
  receive_wait_time_seconds  = 20  # Long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${var.project_name}-processing-${var.environment}"
  }
}

# DynamoDB table for idempotency (prevent duplicate processing)
resource "aws_dynamodb_table" "idempotency" {
  name         = "${var.project_name}-idempotency-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"  # Free tier: 25 GB storage
  hash_key     = "delivery_id"

  attribute {
    name = "delivery_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "${var.project_name}-idempotency-${var.environment}"
  }
}
