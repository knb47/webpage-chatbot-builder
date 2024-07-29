# backend/accounts/tasks.py

from celery import shared_task
from .models import UploadedFile, Deployment
from .deployment.deploy import deploy_user_app
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def deploy_chat_app(self, user_id, config_file_name):
    try:
        uploaded_file = UploadedFile.objects.get(file=config_file_name, user_id=user_id)

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in uploaded_file.file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        result = deploy_user_app(user_id, temp_file_path)

        if result['status'] == 'completed':
            Deployment.objects.create(
                user_id=user_id,
                config_file=uploaded_file,
                endpoint=result['endpoint']
            )
        os.remove(temp_file_path)
        
        return result
    except Exception as e:
        logger.error(f"Error deploying chat app for user {user_id}: {e}")
        return {'status': 'failed', 'error': str(e)}

@shared_task
def test_task():
    return 'Celery is working!'
