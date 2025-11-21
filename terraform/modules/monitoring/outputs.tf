output "webhook_errors_alarm_arn" {
  description = "ARN of webhook errors alarm"
  value       = aws_cloudwatch_metric_alarm.webhook_errors.arn
}

output "dlq_messages_alarm_arn" {
  description = "ARN of DLQ messages alarm"
  value       = aws_cloudwatch_metric_alarm.dlq_messages.arn
}

output "queue_depth_alarm_arn" {
  description = "ARN of queue depth alarm"
  value       = aws_cloudwatch_metric_alarm.queue_depth.arn
}
