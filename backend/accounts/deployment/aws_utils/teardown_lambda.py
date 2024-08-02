import boto3
import os
import logging
import time
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.accounts.models import Deployment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_deletion_to_complete(lambda_client, function_name):
    """Polls the Lambda function's status and waits for any ongoing deletions to complete."""
    max_attempts = 12  # Total 120 seconds wait time
    attempts = 0
    while attempts < max_attempts:
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            update_status = response['Configuration'].get('LastUpdateStatus', 'Successful')
            if update_status != 'InProgress':
                logger.info(f"Deletion complete. LastUpdateStatus: {update_status}")
                return
        except lambda_client.exceptions.ResourceNotFoundException:
            logger.info(f"Function {function_name} no longer exists.")
            return
        logger.info(f"Deletion in progress, waiting... (Attempt {attempts+1}/{max_attempts})")
        time.sleep(10)  # Polling interval
        attempts += 1
    raise TimeoutError("Max polling attempts reached. Lambda function deletion did not complete in time.")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def teardown_user_app(user_id, deployment):
    try:
        bot_name = deployment.chatbot_name
        logger.info(f"Starting teardown for user_id: {user_id}, bot_name: {bot_name}")

        aws_region = os.environ.get('AWS_REGION')
        if not aws_region:
            raise ValueError("AWS_REGION environment variable is not set.")

        function_name = deployment.resource_name
        lambda_client = boto3.client('lambda', region_name=aws_region)
        api_client = boto3.client('apigateway', region_name=aws_region)

        # Wait for any ongoing updates to complete
        wait_for_deletion_to_complete(lambda_client, function_name)

        # Step 1: Delete the Lambda function
        try:
            lambda_client.delete_function(FunctionName=function_name)
            logger.info(f"Deleted Lambda function {function_name}")
        except lambda_client.exceptions.ResourceNotFoundException:
            logger.info(f"Lambda function {function_name} does not exist. Skipping deletion.")

        # Step 2: Remove API Gateway configurations
        api_id = os.environ.get('EXISTING_API_GATEWAY_ID')
        if not api_id:
            raise ValueError("EXISTING_API_GATEWAY_ID environment variable is not set.")

        resources = api_client.get_resources(restApiId=api_id)
        user_resource = next((item for item in resources['items'] if item.get('path') == f"/user/{user_id}/{bot_name}/chat"), None)
        if user_resource:
            resource_id = user_resource['id']
            try:
                api_client.delete_method(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod='ANY'
                )
                logger.info(f"Deleted 'ANY' method for resource {resource_id}")
            except api_client.exceptions.NotFoundException:
                logger.info(f"Method 'ANY' not found for resource {resource_id}. Skipping deletion.")
        else:
            logger.info(f"Resource for user {user_id} and bot {bot_name} not found. Skipping API Gateway teardown.")

        # Step 3: Remove permission for API Gateway to invoke Lambda
        statement_id = f"apigateway-{user_id}-{bot_name}"
        try:
            lambda_client.remove_permission(
                FunctionName=function_name,
                StatementId=statement_id
            )
            logger.info(f"Removed permission statement {statement_id}")
        except lambda_client.exceptions.ResourceNotFoundException:
            logger.info(f"Permission statement {statement_id} does not exist. Skipping permission removal.")

        logger.info("Teardown completed successfully.")

        return {'status': 'completed', 'message': 'Teardown successful'}
    except Exception as e:
        logger.error(f"Error during teardown: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }
