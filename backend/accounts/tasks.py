# backend/accounts/tasks.py

from celery import shared_task
from .models import UploadedFile, Deployment
from .deployment.aws_utils.deploy_lambda import deploy_user_app
from .deployment.aws_utils.teardown_lambda import teardown_user_app
from django.shortcuts import get_object_or_404
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

# backend/accounts/tasks.py

@shared_task(bind=True)
def deploy_chat_app(self, user_id, relative_file_path):
    try:
        logger.info(f"Searching for UploadedFile with path: {relative_file_path} for user: {user_id}")

        # Query using the relative file path
        uploaded_file = UploadedFile.objects.get(file=relative_file_path, user_id=user_id)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in uploaded_file.file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        result = deploy_user_app(user_id, temp_file_path)
        os.remove(temp_file_path)

        if result['status'] == 'completed':
            # Extract bot_name from result or set a default if necessary
            bot_name = result.get('bot_name', f'nameless_bot_{user_id}')

            # Create a Deployment object with correct fields
            deployment = Deployment.objects.create(
                user_id=user_id,
                resource_name=result['resource_name'],
                config_file_path=uploaded_file.file.name,  # Store the relative file path
                config_file_name=uploaded_file.file_name,
                chatbot_name=result['chatbot_name'],
                endpoint=result['endpoint'],
                status='active'
            )
            logger.info(f"Deployment created with resource_name: {deployment.resource_name}")

            return {
                'status': 'completed',
                'endpoint': result['endpoint'],
                'file_path': uploaded_file.file.name,  # Include relative file path
                'file_name': uploaded_file.file_name,  # Include the actual file name
                'deployment_id': deployment.id  # Include the deployment ID
            }

        return {'status': 'failed', 'error': 'Deployment could not be completed.'}
    except UploadedFile.DoesNotExist:
        logger.error(f"UploadedFile with path {relative_file_path} and user {user_id} does not exist.")
        return {'status': 'failed', 'error': 'UploadedFile matching query does not exist.'}
    except Exception as e:
        logger.error(f"Error deploying chat app for user {user_id}: {e}")
        return {'status': 'failed', 'error': str(e)}
    
@shared_task(bind=True)
def teardown_chat_app(self, user_id, deployment_id):
    deployment = get_object_or_404(Deployment, user__id=user_id, id=deployment_id)
    try:
        logger.info(f"Initiating teardown for user_id: {user_id}, chatbot_name: {deployment.chatbot_name}, endpoint: {deployment.endpoint}")
        result = teardown_user_app(user_id, deployment)
        logger.info(f"Teardown result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during teardown: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e)
        }

@shared_task
def test_task():
    return 'Celery is working!'
