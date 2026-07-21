"""boto3 client factory — real AWS by default, LocalStack when configured.

Set AWS_ENDPOINT_URL (e.g. http://localstack:4566) to aim every AWS call at a
LocalStack edge instead of real AWS. Leave it unset in production; nothing
else changes.

AWS_PUBLIC_ENDPOINT_URL is the same edge as reachable from the *user's
browser* (e.g. http://localhost:4566 when Django runs in compose but the
recruiter clicks from the host). Used only to build invoke URLs.
"""

import os

import boto3

AWS_ENDPOINT_URL = os.environ.get("AWS_ENDPOINT_URL") or None
AWS_PUBLIC_ENDPOINT_URL = os.environ.get("AWS_PUBLIC_ENDPOINT_URL") or AWS_ENDPOINT_URL


def aws_client(service, region_name):
    return boto3.client(service, region_name=region_name, endpoint_url=AWS_ENDPOINT_URL)


def invoke_url(api_id, region, stage, path):
    """Public URL for an API Gateway route — AWS or LocalStack format."""
    path = path.lstrip("/")
    if AWS_PUBLIC_ENDPOINT_URL:
        # LocalStack REST-API invoke format.
        return f"{AWS_PUBLIC_ENDPOINT_URL}/restapis/{api_id}/{stage}/_user_request_/{path}"
    return f"https://{api_id}.execute-api.{region}.amazonaws.com/{stage}/{path}"
