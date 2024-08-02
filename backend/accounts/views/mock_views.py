# Mock views to circumvent the need for a Celery worker or long-running tasks

from .base_views import *
from ..tasks_mock import mock_deploy_chat_app, mock_teardown_operation
import time


@login_required
def deploy_view(request, file_id):
    config_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)

    # Directly calling the mock function synchronously for simplicity in development
    result = mock_deploy_chat_app(user_id=request.user.id, relative_file_path=config_file.file.name)

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
    # simulate async task status check
    time.sleep(3)
    
    return JsonResponse({
        'status': 'completed',
        'endpoint': 'dummy_endpoint',
        'file_path': 'dummy_file_path',
        'file_name': 'dummy_file_name',
        'deployment_id': 'dummy_deployment_id'
    })

    # return JsonResponse({
    #     'status': 'failed',
    #     'endpoint': 'dummy_endpoint',
    #     'file_path': 'dummy_file_path',
    #     'file_name': 'dummy_file_name',
    #     'deployment_id': 'dummy_deployment_id'
    # })


@login_required
def teardown_view(request, deployment_id):
    # Simulate fetching a deployment object (mock)
    deployment = get_object_or_404(Deployment, id=deployment_id, user=request.user)

    if deployment.status == 'inactive':
        return JsonResponse({
            'status': 'failed',
            'message': 'Deployment is already inactive.'
        })

    # Mock a teardown operation
    result = mock_teardown_operation(user_id=request.user.id, endpoint=deployment.endpoint)

    # Generate a mock task ID
    task_id = 'mock-teardown-task-id'
    response = {
        'task_id': task_id,
        'status': result['status'],
        'endpoint': result.get('endpoint', ''),
        'message': result.get('message', ''),
    }
    return JsonResponse(response)

@login_required
def teardown_status_view(request, task_id):
    # Simulate async task status check
    time.sleep(3)  # Delay to simulate processing time

    task_state = 'SUCCESS'
    if task_state == 'SUCCESS':
        # Mock response to simulate completed teardown
        result = {
            'status': 'completed',
            'endpoint': 'mock_endpoint',
            'message': 'Teardown completed successfully.'
        }

    if result.get('status') == 'completed':
        # mark deployment object as inactive
        deployment = Deployment.objects.get(user=request.user, config_file_name='chat_full.yaml')
        deployment.status = 'inactive'
        deployment.save()

    # Mock response to simulate completed teardown
    return JsonResponse({
        'status': 'completed',
        'deployment_status': deployment.status,
        'endpoint': 'mock_endpoint',
        'message': 'Teardown completed successfully.'
    })
