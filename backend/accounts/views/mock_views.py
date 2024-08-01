# Mock views to circumvent the need for a Celery worker or long-running tasks

from .base_views import *
from ..tasks_mock import mock_deploy_chat_app


@login_required
def deploy_view(request, file_id):
    config_file = get_object_or_404(
        UploadedFile, id=file_id, user=request.user)

    # Simulate deployment using mock function
    logger.info(f"Mock: Deploying chat app for file {config_file.file.name}")
    # Directly calling the mock function synchronously for simplicity in development
    result = mock_deploy_chat_app(
        user_id=request.user.id, relative_file_path=config_file.file.name)

    # Mock task result without async
    task_id = 'mock-task-id'  # Simulate a task ID
    response = {
        'task_id': task_id,
        'status': result['status'],
        'endpoint': result.get('endpoint', ''),
        'file_path': result.get('file_path', ''),
        'file_name': result.get('file_name', ''),
        'deployment_id': result.get('deployment_id', '')
    }
    return JsonResponse(response)


@login_required
def deployment_status_view(request, task_id):
    return JsonResponse({
      'status': 'completed',
      'endpoint': 'dummy_endpoint',
      'file_path': 'dummy_file_path',
      'file_name': 'dummy_file_name',
      'deployment_id': 'dummy_deployment_id'
    })
