# Monitoring Module
# CloudWatch alarms and dashboards for quality-agent

# Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "webhook_errors" {
  alarm_name          = "${var.project_name}-webhook-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Webhook receiver Lambda errors"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = var.webhook_lambda_name
  }
}

# Alarm for SQS dead letter queue
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project_name}-dlq-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Messages in dead letter queue"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = var.dlq_name
  }
}

# Alarm for processing queue depth
resource "aws_cloudwatch_metric_alarm" "queue_depth" {
  alarm_name          = "${var.project_name}-queue-depth-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 100
  alarm_description   = "Processing queue depth too high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = var.processing_queue_name
  }
}
