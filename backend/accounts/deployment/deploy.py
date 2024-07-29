import boto3
import os
import shutil
import yaml
from zipfile import ZipFile
from celery import shared_task
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_script_dir = os.path.dirname(os.path.abspath(__file__))
skeleton_dir = os.path.join(current_script_dir, "./app_skeleton_code")

@shared_task(bind=True)
def deploy_user_app(self, user_id, config_file_path):
    try:
        logger.info(f"Starting deployment for user_id: {user_id}, config_file_path: {config_file_path}")
        environment = os.environ.get('DJANGO_ENV', 'development')
        logger.info(f"Environment: {environment}")

        aws_region = os.environ.get('AWS_REGION')
        lambda_role = os.environ.get('LAMBDA_EXECUTION_ROLE')
        if not aws_region or not lambda_role:
            raise ValueError("AWS_REGION or LAMBDA_EXECUTION_ROLE environment variable is not set.")

        if environment == 'development':
            return {'status': 'completed', 'endpoint': f"https://example-api-id.execute-api.example-region.amazonaws.com/prod/user/{user_id}/nameless_bot/chat", 'config_file_path': config_file_path}

        user_dir = f"/tmp/{user_id}"

        # Step 1: Copy Skeleton Directory
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
        shutil.copytree(skeleton_dir, user_dir)
        logger.info(f"Copied skeleton directory to {user_dir}")

        # Step 2: Insert Config File
        user_config_file = os.path.join(user_dir, "config.yaml")
        shutil.copyfile(config_file_path, user_config_file)
        logger.info(f"Copied config file to {user_config_file}")

        # Step 3: Extract bot_name from the Config File
        with open(config_file_path, 'r') as file:
            config = yaml.safe_load(file)
            bot_name = config.get('bot_name', f'nameless_bot_{user_id}')
            logger.info(f"Extracted bot_name: {bot_name} from config file")

        # Step 4: Package the Application
        package_path = f"/tmp/{user_id}.zip"
        with ZipFile(package_path, 'w') as zipf:
            for root, dirs, files in os.walk(user_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), user_dir))
        logger.info(f"Packaged application at {package_path}")

        # Step 5: Deploy to AWS Lambda using boto3
        lambda_client = boto3.client('lambda', region_name=aws_region)
        api_client = boto3.client('apigateway', region_name=aws_region)

        # Upload Lambda function
        with open(package_path, 'rb') as f:
            lambda_zip = f.read()

        function_name = f"user_app_{user_id}_{bot_name}"
        
        try:
            response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.8',
                Role=lambda_role,
                Handler='app.Lambda_Service.handler',
                Code={'ZipFile': lambda_zip},
                Environment={'Variables': {'USER_CONFIG': user_config_file}},
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
            response = lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=lambda_zip,
            )
            logger.info(f"Updated Lambda function {function_name}")

        # Create or update API Gateway
        api_id = os.environ.get('EXISTING_API_GATEWAY_ID')
        if not api_id:
            raise ValueError("EXISTING_API_GATEWAY_ID environment variable is not set.")

        resources = api_client.get_resources(restApiId=api_id)

        # Find the /user/{proxy+} resource
        user_resource = next((item for item in resources['items'] if item.get('path') == '/user/{proxy+}'), None)
        if not user_resource:
            logger.error("The /user/{proxy+} resource does not exist in the API Gateway")
            raise ValueError("Required API Gateway resource not found")

        resource_id = user_resource['id']

# Check if the method already exists
        try:
            existing_method = api_client.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='ANY'
            )
            logger.info("Method 'ANY' already exists for this resource. Updating integration.")
        except api_client.exceptions.NotFoundException:
            # If the method doesn't exist, create it
            api_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='ANY',
                authorizationType='NONE'
            )
            logger.info("Created new 'ANY' method for the resource.")

        # Update the integration (this will create or update as necessary)
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

        api_client.create_deployment(
            restApiId=api_id,
            stageName='prod'
        )

        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=f"apigateway-{user_id}-{bot_name}",
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f"arn:aws:execute-api:{aws_region}:{os.environ['AWS_ACCOUNT_ID']}:{api_id}/*/*/user/*"
        )

        unique_endpoint = f"https://{api_id}.execute-api.{aws_region}.amazonaws.com/prod/user/{user_id}/{bot_name}/chat"
        logger.info(f"Deployment completed. Endpoint: {unique_endpoint}")

        # Clean up
        os.remove(package_path)
        shutil.rmtree(user_dir)

        return {'status': 'completed', 'endpoint': unique_endpoint, 'config_file_path': config_file_path}
    except Exception as e:
        logger.error(f"Error during deployment: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'config_file_path': config_file_path  # Include this to maintain consistent structure
        }