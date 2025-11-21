output "events_bucket_name" {
  description = "S3 bucket name for webhook events"
  value       = aws_s3_bucket.events.id
}

output "events_bucket_arn" {
  description = "S3 bucket ARN for webhook events"
  value       = aws_s3_bucket.events.arn
}

output "processing_queue_url" {
  description = "SQS queue URL for processing"
  value       = aws_sqs_queue.processing.url
}

output "processing_queue_arn" {
  description = "SQS queue ARN for processing"
  value       = aws_sqs_queue.processing.arn
}

output "processing_queue_name" {
  description = "SQS queue name for processing"
  value       = aws_sqs_queue.processing.name
}

output "dlq_url" {
  description = "Dead letter queue URL"
  value       = aws_sqs_queue.dlq.url
}

output "dlq_arn" {
  description = "Dead letter queue ARN"
  value       = aws_sqs_queue.dlq.arn
}

output "dlq_name" {
  description = "Dead letter queue name"
  value       = aws_sqs_queue.dlq.name
}

output "idempotency_table_name" {
  description = "DynamoDB table name for idempotency"
  value       = aws_dynamodb_table.idempotency.name
}

output "idempotency_table_arn" {
  description = "DynamoDB table ARN for idempotency"
  value       = aws_dynamodb_table.idempotency.arn
}
