from .base_views import *

# Celery / long-running tasks for deployment are defined here for production
from ..tasks import deploy_chat_app

@login_required
def deploy_view(request, file_id):
    config_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    task = deploy_chat_app.apply_async(args=[request.user.id, config_file.file.name])  # file.name includes the relative path
    return JsonResponse({'task_id': task.id})

@login_required
def deployment_status_view(request, task_id):
    task = deploy_chat_app.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        result = task.result
        if result.get('status') == 'completed':
            return JsonResponse({
                'status': 'completed',
                'endpoint': result.get('endpoint'),
                'file_path': result.get('file_path'),  # Retrieve the relative file path directly from the task result
                'file_name': result.get('file_name'),  # Retrieve the file name directly from the task result
                'deployment_id': result.get('deployment_id')  # Retrieve the deployment ID directly from the task result
            })
        else:
            return JsonResponse({'status': 'failed', 'error': result.get('error', 'Unknown error')})
    elif task.state == 'FAILURE':
        return JsonResponse({'status': 'failed', 'error': str(task.info)})
    else:
        return JsonResponse({'status': 'pending'})
    
@login_required
def deployment_status_view(request, task_id):
    task = deploy_chat_app.AsyncResult(task_id)
    if task.state == 'SUCCESS':
        result = task.result
        if result.get('status') == 'completed':
            return JsonResponse({
                'status': 'completed',
                'endpoint': result.get('endpoint'),
                'file_path': result.get('file_path'),  # Retrieve the relative file path directly from the task result
                'file_name': result.get('file_name'),  # Retrieve the file name directly from the task result
                'deployment_id': result.get('deployment_id')  # Retrieve the deployment ID directly from the task result
            })
        else:
            return JsonResponse({'status': 'failed', 'error': result.get('error', 'Unknown error')})
    elif task.state == 'FAILURE':
        return JsonResponse({'status': 'failed', 'error': str(task.info)})
    else:
        return JsonResponse({'status': 'pending'})