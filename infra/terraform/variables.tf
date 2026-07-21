variable "project" {
  description = "Resource name prefix."
  type        = string
  default     = "chapp"
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "aws_endpoint" {
  description = "AWS API endpoint. Set to the LocalStack edge (default) for local development; set to \"\" to target real AWS."
  type        = string
  default     = "http://localhost:4566"
}
