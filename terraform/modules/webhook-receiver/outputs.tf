output "function_url" {
  description = "Lambda Function URL for GitHub webhook"
  value       = aws_lambda_function_url.webhook.function_url
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.webhook_receiver.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.webhook_receiver.arn
}

output "lambda_role_arn" {
  description = "Lambda IAM role ARN"
  value       = aws_iam_role.lambda.arn
}
