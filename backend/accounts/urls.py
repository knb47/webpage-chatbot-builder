# ./backend/accounts/urls.py

# backend/accounts/urls.py

from django.urls import path
from .views import FileUploadView, FileListView, library_view, CreateUserView, SignUpView, delete_file, deploy_view, deployment_status_view, deployments_view

urlpatterns = [
    # API routes
    path('register/', CreateUserView.as_view(), name='account-create'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('deploy/<int:file_id>/', deploy_view, name='deploy'),
    path('deployment_status/<str:task_id>/', deployment_status_view, name='deployment_status'),
    path('deployments/', deployments_view, name='deployments'),
    
    # Non-API routes
    path('library/', library_view, name='library'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('delete-file/<int:file_id>/', delete_file, name='delete_file'),
]