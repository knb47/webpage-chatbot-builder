import boto3
import os
import shutil
import yaml
from zipfile import ZipFile
from celery import shared_task
import logging
import time
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.accounts.models import Deployment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_script_dir)
deployment_package_path = os.path.join(parent_dir, "deployment_package.zip")

def wait_for_update_to_complete(lambda_client, function_name):
    """Polls the Lambda function's status and waits for any ongoing updates to complete."""
    max_attempts = 12  # Total 120 seconds wait time
    attempts = 0
    while attempts < max_attempts:
        response = lambda_client.get_function(FunctionName=function_name)
        update_status = response['Configuration'].get('LastUpdateStatus', 'Successful')
        if update_status != 'InProgress':
            logger.info(f"Update complete. LastUpdateStatus: {update_status}")
            return
        logger.info(f"Update in progress, waiting... (Attempt {attempts+1}/{max_attempts})")
        time.sleep(10)  # Polling interval
        attempts += 1
    raise TimeoutError("Max polling attempts reached. Lambda function update did not complete in time.")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def update_lambda_function(lambda_client, function_name, zip_file, environment_vars):
    """Updates Lambda function code and configuration with retry mechanism."""
    wait_for_update_to_complete(lambda_client, function_name)
    lambda_client.update_function_code(FunctionName=function_name, ZipFile=zip_file)
    wait_for_update_to_complete(lambda_client, function_name)
    lambda_client.update_function_configuration(
        FunctionName=function_name,
        Environment={'Variables': environment_vars},
        Timeout=30  # Set timeout to 30 seconds
    )
    wait_for_update_to_complete(lambda_client, function_name)

@shared_task(bind=True)
def deploy_user_app(self, user_id, temp_file_path):
    try:
        logger.info(f"Starting deployment for user_id: {user_id}, temp_file_path: {temp_file_path}")
        environment = os.environ.get('DJANGO_ENV', 'development')
        logger.info(f"Environment: {environment}")

        aws_region = os.environ.get('AWS_REGION')
        lambda_role = os.environ.get('LAMBDA_EXECUTION_ROLE')
        if not aws_region or not lambda_role:
            raise ValueError("AWS_REGION or LAMBDA_EXECUTION_ROLE environment variable is not set.")

        # Create a temporary working directory
        user_dir = f"/tmp/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        # Step 1: Copy the deployment package to the temporary directory
        temp_package_path = os.path.join(user_dir, "deployment_package.zip")
        shutil.copyfile(deployment_package_path, temp_package_path)
        logger.info(f"Copied deployment package to {temp_package_path}")

        # Step 2: Add the config file to the deployment package
        with ZipFile(temp_package_path, 'a') as zipf:
            zipf.write(temp_file_path, os.path.join("app", "config", "config.yaml"))
        logger.info(f"Added config file to {temp_package_path}")

        # Verify the contents of the ZIP file
        with ZipFile(temp_package_path, 'r') as zipf:
            if 'lambda_function.py' not in zipf.namelist():
                logger.error("lambda_function.py not found in the root of the zip file")
                raise FileNotFoundError("lambda_function.py not found in the root of the zip file")
            logger.info("Verified lambda_function.py is present in the root of the zip file")

        # Step 3: Extract bot_name from the Config File
        with open(temp_file_path, 'r') as file:
            config = yaml.safe_load(file)
            bot_name = config.get('bot_name', f'nameless_bot_{user_id}')
            logger.info(f"Extracted bot_name: {bot_name} from config file")

        # Step 4: Upload the modified deployment package to Lambda
        with open(temp_package_path, 'rb') as f:
            lambda_zip = f.read()

        # Step 5: Create or update Lambda function
        sanitize_name = lambda bot_name: ''.join(c for c in bot_name if c.isalnum() or c in '-_') # adhere to aws lambda naming restrictions
        bot_name_clean = sanitize_name(bot_name)
        function_name = f"user-app-{user_id}-{bot_name_clean}"

        lambda_client = boto3.client('lambda', region_name=aws_region)
        api_client = boto3.client('apigateway', region_name=aws_region)

        environment_vars = {
            'USER_CONFIG': os.path.join("app", "config", "config.yaml"),
            'OPENAI_API_KEY': os.environ.get("OPENAI_API_KEY")
        }

        # Try to create or update Lambda function
        try:
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.10',
                Role=lambda_role,
                Handler='lambda_function.handler',
                Code={'ZipFile': lambda_zip},
                Environment={'Variables': environment_vars},
                Timeout=30,  # Set timeout to 30 seconds
                Tags={
                    'Project': 'user-app-service',
                    'Environment': 'production',
                    'Feature': 'user-chat-deployment',
                    'User': str(user_id),
                    'Bot': bot_name
                },
            )
            logger.info(f"Created Lambda function {function_name}")
        except lambda_client.exceptions.ResourceConflictException:
            # If function exists, update the code and the configuration
            logger.info(f"Lambda function {function_name} already exists. Updating...")
            update_lambda_function(lambda_client, function_name, lambda_zip, environment_vars)
            logger.info(f"Updated Lambda function {function_name}")

        # Update API Gateway configurations
        api_id = os.environ.get('EXISTING_API_GATEWAY_ID')
        if not api_id:
            raise ValueError("EXISTING_API_GATEWAY_ID environment variable is not set.")

        resources = api_client.get_resources(restApiId=api_id)
        user_resource = next((item for item in resources['items'] if item.get('path') == '/user/{proxy+}'), None)
        if not user_resource:
            logger.error("The /user/{proxy+} resource does not exist in the API Gateway")
            raise ValueError("Required API Gateway resource not found")

        resource_id = user_resource['id']
        try:
            existing_method = api_client.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='ANY'
            )
            logger.info("Method 'ANY' already exists for this resource. Skipping method creation.")
        except api_client.exceptions.NotFoundException:
            api_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='ANY',
                authorizationType='NONE'
            )
            logger.info("Created new 'ANY' method for the resource.")

        # Update integration and deploy
        try:
            api_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='ANY',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f"arn:aws:apigateway:{aws_region}:lambda:path/2015-03-31/functions/arn:aws:lambda:{aws_region}:{os.environ['AWS_ACCOUNT_ID']}:function:{function_name}/invocations"
            )
            logger.info("Updated integration for 'ANY' method.")
        except Exception as e:
            logger.error(f"Error updating integration: {str(e)}")
            raise

        # Finalize API Gateway configuration
        api_client.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )

        # Set permissions for API Gateway to invoke Lambda
        statement_id = f"apigateway-{user_id}-{bot_name}"
        try:
            lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{aws_region}:{os.environ['AWS_ACCOUNT_ID']}:{api_id}/*/*/user/*"
            )
        except lambda_client.exceptions.ResourceConflictException:
            logger.info(f"Permission statement {statement_id} already exists. Skipping permission creation.")

        unique_endpoint = f"https://{api_id}.execute-api.{aws_region}.amazonaws.com/prod/user/{user_id}/{bot_name}/chat"
        logger.info(f"Deployment completed. Endpoint: {unique_endpoint}")

        # Clean up
        os.remove(temp_package_path)
        shutil.rmtree(user_dir)

        return {
            'status': 'completed',
            'resource_name': function_name,
            'endpoint': unique_endpoint, 
            'temp_file_path': temp_file_path,
            'chatbot_name': bot_name
        }
    except Exception as e:
        logger.error(f"Error during deployment: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'temp_file_path': temp_file_path
        }
