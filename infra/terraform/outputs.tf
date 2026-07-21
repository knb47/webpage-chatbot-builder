# These outputs map 1:1 onto the control plane's environment variables.

output "api_gateway_id" {
  description = "-> EXISTING_API_GATEWAY_ID"
  value       = aws_api_gateway_rest_api.user_apps.id
}

output "lambda_execution_role_arn" {
  description = "-> LAMBDA_EXECUTION_ROLE"
  value       = aws_iam_role.lambda_execution.arn
}

output "tenant_configs_bucket" {
  description = "S3 bucket holding uploaded tenant configs"
  value       = aws_s3_bucket.tenant_configs.bucket
}

output "aws_region" {
  description = "-> AWS_REGION"
  value       = var.aws_region
}
