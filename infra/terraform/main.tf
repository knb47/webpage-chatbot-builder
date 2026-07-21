# Base infrastructure for the multitenant chat-agent platform.
#
# Provisions the shared, per-environment resources that the control plane's
# deploy pipeline (backend/accounts/deployment/aws_utils/deploy_lambda.py)
# expects to already exist:
#
#   - IAM execution role for tenant Lambdas   -> LAMBDA_EXECUTION_ROLE
#   - shared REST API with /user/{proxy+}     -> EXISTING_API_GATEWAY_ID
#   - S3 bucket for uploaded tenant configs
#
# By default it targets LocalStack (var.aws_endpoint). Point it at real AWS by
# applying with -var aws_endpoint="" — the resources are identical.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
}

locals {
  use_localstack = var.aws_endpoint != ""
}

provider "aws" {
  region = var.aws_region

  # LocalStack: dummy credentials + edge endpoint. All three blocks collapse
  # to normal AWS behavior when aws_endpoint is empty.
  access_key                  = local.use_localstack ? "test" : null
  secret_key                  = local.use_localstack ? "test" : null
  skip_credentials_validation = local.use_localstack
  skip_metadata_api_check     = local.use_localstack
  skip_requesting_account_id  = local.use_localstack
  s3_use_path_style           = local.use_localstack

  dynamic "endpoints" {
    for_each = local.use_localstack ? [1] : []
    content {
      lambda     = var.aws_endpoint
      apigateway = var.aws_endpoint
      s3         = var.aws_endpoint
      iam        = var.aws_endpoint
      sts        = var.aws_endpoint
      logs       = var.aws_endpoint
      cloudwatch = var.aws_endpoint
    }
  }
}

# ---------------------------------------------------------------- IAM ------

resource "aws_iam_role" "lambda_execution" {
  name = "${var.project}-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ------------------------------------------------------- API Gateway -------

# One shared REST API fronts every tenant Lambda; the deploy pipeline wires an
# AWS_PROXY integration on /user/{proxy+} per deployment.
resource "aws_api_gateway_rest_api" "user_apps" {
  name        = "${var.project}-user-apps"
  description = "Shared gateway routing /user/* to per-tenant chat-agent Lambdas"
}

resource "aws_api_gateway_resource" "user" {
  rest_api_id = aws_api_gateway_rest_api.user_apps.id
  parent_id   = aws_api_gateway_rest_api.user_apps.root_resource_id
  path_part   = "user"
}

resource "aws_api_gateway_resource" "user_proxy" {
  rest_api_id = aws_api_gateway_rest_api.user_apps.id
  parent_id   = aws_api_gateway_resource.user.id
  path_part   = "{proxy+}"
}

# ----------------------------------------------------------------- S3 ------

resource "aws_s3_bucket" "tenant_configs" {
  bucket        = "${var.project}-tenant-configs"
  force_destroy = true
}
